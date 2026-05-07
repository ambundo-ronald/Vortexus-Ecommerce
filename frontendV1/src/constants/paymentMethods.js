export const PAYMENT_METHOD_CODES = {
  MPESA: "mpesa",
  AIRTEL_MONEY: "airtel_money",
  CREDIT_CARD: "credit_card",
  DEBIT_CARD: "debit_card",
  BANK_TRANSFER: "bank_transfer",
  CASH_ON_DELIVERY: "cash_on_delivery"
};

export const PREPAYMENT_METHODS = new Set([
  PAYMENT_METHOD_CODES.MPESA,
  PAYMENT_METHOD_CODES.AIRTEL_MONEY,
  PAYMENT_METHOD_CODES.CREDIT_CARD,
  PAYMENT_METHOD_CODES.DEBIT_CARD
]);
