import { useCallback, useEffect, useState } from "react";

import { paymentsApi } from "../api/payments.api";
import {
  PAYMENT_CONFIRMATION_TIMEOUT_MS,
  isPaymentComplete,
  isPaymentFailed
} from "../utils/payment";

const POLL_DELAY_MS = 4000;
const MAX_PAYMENT_POLLS = 30;

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Payment could not be completed.";
}

function delay(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export function usePayment({ auto = true } = {}) {
  const [methods, setMethods] = useState([]);
  const [payment, setPayment] = useState(null);
  const [loading, setLoading] = useState(Boolean(auto));
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState("");

  const loadMethods = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const payload = await paymentsApi.methods();
      const items = payload?.results || payload?.methods || payload || [];
      setMethods(Array.isArray(items) ? items : []);
      return items;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  const initializePayment = useCallback(async ({
    method,
    phoneNumber = "",
    payerEmail = "",
    customerName = "",
    cardDetails = {}
  }) => {
    setProcessing(true);
    setError("");
    try {
      let payload;
      if (method === "credit_card" || method === "debit_card") {
        payload = await paymentsApi.initializeCard({
          method,
          payer_email: payerEmail,
          payment_token: cardDetails.paymentToken || (method === "debit_card" ? "tok_test_debit" : "tok_test_visa"),
          card_brand: cardDetails.cardBrand || (method === "debit_card" ? "debit" : "visa"),
          last4: cardDetails.last4 || (method === "debit_card" ? "0005" : "4242"),
          expiry_month: cardDetails.expiryMonth || 12,
          expiry_year: cardDetails.expiryYear || 2030,
          holder_name: cardDetails.holderName || "Online Customer"
        });
      } else if (method === "mpesa") {
        payload = await paymentsApi.initializeMpesa({ phone_number: phoneNumber, payer_email: payerEmail });
      } else if (method === "pesapal") {
        payload = await paymentsApi.initializePesapal({
          phone_number: phoneNumber,
          payer_email: payerEmail,
          customer_name: customerName
        });
      } else if (method === "airtel_money") {
        payload = await paymentsApi.initializeAirtel({ phone_number: phoneNumber, payer_email: payerEmail });
      } else {
        payload = await paymentsApi.initialize({
          method,
          phone_number: phoneNumber,
          payer_email: payerEmail
        });
      }
      const createdPayment = payload?.payment || null;
      if (!createdPayment?.reference) {
        throw new Error("Payment was not created. Choose another payment option.");
      }
      setPayment(createdPayment);
      return createdPayment;
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setProcessing(false);
    }
  }, []);

  const getPaymentStatus = useCallback(async (reference, method = "") => {
    let payload;
    if (method === "mpesa") {
      payload = await paymentsApi.mpesaStatus(reference);
    } else if (method === "pesapal") {
      payload = await paymentsApi.pesapalStatus(reference);
    } else if (method === "airtel_money") {
      payload = await paymentsApi.airtelStatus(reference);
    } else {
      payload = await paymentsApi.detail(reference);
    }
    const nextPayment = payload?.payment || null;
    if (nextPayment) setPayment(nextPayment);
    return nextPayment;
  }, []);

  const waitForPayment = useCallback(async (
    createdPayment,
    {
      maxPolls = MAX_PAYMENT_POLLS,
      delayMs = POLL_DELAY_MS,
      timeoutMs = PAYMENT_CONFIRMATION_TIMEOUT_MS,
      onUpdate
    } = {}
  ) => {
    if (!createdPayment?.reference) {
      throw new Error("Payment was not created. Choose another payment option.");
    }

    if (isPaymentComplete(createdPayment)) return createdPayment;
    if (isPaymentFailed(createdPayment)) {
      throw new Error("Payment was not completed. Choose another payment option.");
    }

    setProcessing(true);
    setError("");
    try {
      const startedAt = Date.now();
      for (let attempt = 0; attempt < maxPolls; attempt += 1) {
        if (Date.now() - startedAt >= timeoutMs) break;
        if (attempt > 0) await delay(delayMs);
        const nextPayment = await getPaymentStatus(createdPayment.reference, createdPayment.method);
        onUpdate?.(nextPayment);
        if (isPaymentComplete(nextPayment)) return nextPayment;
        if (isPaymentFailed(nextPayment)) {
          throw new Error("Payment was not completed. Choose another payment option.");
        }
      }

      throw new Error("Payment was not confirmed within 5 minutes. Prompt your phone again or choose another method.");
    } catch (error) {
      setError(messageFromError(error));
      throw error;
    } finally {
      setProcessing(false);
    }
  }, [getPaymentStatus]);

  useEffect(() => {
    if (auto) void loadMethods();
  }, [auto, loadMethods]);

  return {
    methods,
    payment,
    loading,
    processing,
    error,
    setError,
    loadMethods,
    initializePayment,
    getPaymentStatus,
    waitForPayment
  };
}
