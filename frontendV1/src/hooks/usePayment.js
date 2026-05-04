import { useCallback, useEffect, useState } from "react";

import { paymentsApi } from "../api/payments.api";

function messageFromError(error) {
  return error?.normalized?.message || error?.message || "Payment could not be completed.";
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

  const initializePayment = useCallback(async ({ method, phoneNumber = "", payerEmail = "" }) => {
    setProcessing(true);
    setError("");
    try {
      let payload;
      if (method === "credit_card" || method === "debit_card") {
        payload = await paymentsApi.initializeCard({
          method,
          payer_email: payerEmail,
          payment_token: "tok_test_visa",
          card_brand: method === "debit_card" ? "debit" : "visa",
          last4: method === "debit_card" ? "0005" : "4242",
          expiry_month: 12,
          expiry_year: 2030,
          holder_name: "Online Customer"
        });
      } else if (method === "mpesa") {
        payload = await paymentsApi.initializeMpesa({ phone_number: phoneNumber, payer_email: payerEmail });
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
    initializePayment
  };
}
