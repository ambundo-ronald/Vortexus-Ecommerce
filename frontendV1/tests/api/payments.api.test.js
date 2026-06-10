jest.mock("../../src/api/axiosClient", () => ({
  __esModule: true,
  default: {
    get: jest.fn(),
    post: jest.fn()
  }
}));

jest.mock("../../src/constants/apiEndpoints", () => ({
  ENDPOINTS: {
    payments: {
      methods: "/checkout/payments/methods/",
      sessions: "/checkout/payments/",
      session: (reference) => `/checkout/payments/${reference}/`,
      confirm: (reference) => `/checkout/payments/${reference}/confirm/`,
      mpesaInit: "/checkout/payments/mpesa/initiate/",
      mpesaStatus: (reference) => `/checkout/payments/mpesa/${reference}/status/`,
      pesapalInit: "/checkout/payments/pesapal/initiate/",
      pesapalStatus: (reference) => `/checkout/payments/pesapal/${reference}/status/`,
      airtelInit: "/checkout/payments/airtel-money/initiate/",
      airtelStatus: (reference) => `/checkout/payments/airtel-money/${reference}/status/`,
      cardInit: "/checkout/payments/cards/initiate/"
    }
  }
}));

import apiClient from "../../src/api/axiosClient";
import { paymentsApi } from "../../src/api/payments.api";

describe("paymentsApi", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  test("loads configured payment methods", async () => {
    apiClient.get.mockResolvedValue({ data: { results: [{ code: "mpesa" }] } });

    await expect(paymentsApi.methods()).resolves.toEqual({ results: [{ code: "mpesa" }] });
    expect(apiClient.get).toHaveBeenCalledWith("/checkout/payments/methods/");
  });

  test("initializes and checks an M-Pesa payment", async () => {
    apiClient.post.mockResolvedValue({ data: { payment: { reference: "PAY-1" } } });
    apiClient.get.mockResolvedValue({ data: { payment: { reference: "PAY-1", status: "paid" } } });

    await paymentsApi.initializeMpesa({ phone_number: "+254700000001" });
    await paymentsApi.mpesaStatus("PAY-1");

    expect(apiClient.post).toHaveBeenCalledWith(
      "/checkout/payments/mpesa/initiate/",
      { phone_number: "+254700000001" }
    );
    expect(apiClient.get).toHaveBeenCalledWith("/checkout/payments/mpesa/PAY-1/status/");
  });

  test("initializes Pesapal and card provider flows", async () => {
    apiClient.post.mockResolvedValue({ data: { payment: { reference: "PAY-2" } } });

    await paymentsApi.initializePesapal({ payer_email: "buyer@example.com" });
    await paymentsApi.initializeCard({ method: "credit_card", payment_token: "tok_test_visa" });

    expect(apiClient.post).toHaveBeenNthCalledWith(
      1,
      "/checkout/payments/pesapal/initiate/",
      { payer_email: "buyer@example.com" }
    );
    expect(apiClient.post).toHaveBeenNthCalledWith(
      2,
      "/checkout/payments/cards/initiate/",
      { method: "credit_card", payment_token: "tok_test_visa" }
    );
  });
});
