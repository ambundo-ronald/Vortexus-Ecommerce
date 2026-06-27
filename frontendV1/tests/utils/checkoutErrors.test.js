import {
  checkoutErrorCode,
  checkoutErrorView,
  checkoutToastPayload
} from "../../src/utils/checkoutErrors";

describe("checkout error utilities", () => {
  test("maps missing delivery information during checkout preview", () => {
    const view = checkoutErrorView({
      normalized: {
        message: "Shipping address is required.",
        status: 400,
        code: "validation_error"
      }
    }, "preview");

    expect(view).toMatchObject({
      code: "shipping_missing",
      tone: "warning",
      title: "Delivery details needed",
      actionPath: "/checkout/shipping"
    });
  });

  test("maps payment provider failures to a recoverable payment message", () => {
    const view = checkoutErrorView(new Error("Payment was not completed. Choose another payment option."), "payment");

    expect(view).toMatchObject({
      code: "payment_failed",
      tone: "warning",
      title: "Payment was not completed",
      actionPath: "/checkout/payment"
    });
  });

  test("maps order placement stock issues back to the cart", () => {
    const view = checkoutErrorView({
      response: {
        status: 400,
        data: {
          error: {
            code: "validation_error",
            errors: {
              basket: ["A cart item is no longer available."]
            }
          }
        }
      }
    }, "place_order");

    expect(view).toMatchObject({
      code: "cart_item_unavailable",
      actionLabel: "Review cart",
      actionPath: "/checkout/cart"
    });
    expect(view.message).toBe("A cart item is no longer available.");
  });

  test("uses safe customer copy for server errors", () => {
    const view = checkoutErrorView({
      normalized: {
        message: "Internal Server Error: database stack trace",
        status: 500,
        code: "server_error"
      }
    }, "place_order");

    expect(view).toMatchObject({
      code: "server_error",
      title: "Checkout is temporarily unavailable"
    });
    expect(view.message).toBe("Something went wrong on our side. Try again shortly.");
  });

  test("creates toast payloads from checkout error views", () => {
    expect(checkoutToastPayload(new Error("Payment is still pending."), "payment_status")).toMatchObject({
      tone: "info",
      title: "Payment still pending"
    });
  });

  test("returns unknown for unmatched normalized errors", () => {
    expect(checkoutErrorCode({ message: "No match", status: 400, code: "validation_error" })).toBe("unknown_error");
  });
});
