import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import { siteResources } from "./locales/siteTranslations.generated.js";

const supportedLanguages = ["en", "sw", "fr", "ar", "hi", "zh"];
const savedLanguage = localStorage.getItem("reesolmart-language");
const browserLanguages = [...(navigator.languages || []), navigator.language].filter(Boolean);
const browserLanguage = browserLanguages
  .map((language) => language.toLowerCase().split("-")[0])
  .find((language) => supportedLanguages.includes(language));
const initialLanguage = supportedLanguages.includes(savedLanguage)
  ? savedLanguage
  : browserLanguage || "en";

const resources = {
  en: {
    translation: {
      navigation: { primary: "Primary", shop: "Shop" },
      account: {
        greeting: "Hi, {{name}}",
        myAccount: "My Account",
        orders: "Orders",
        inbox: "Inbox",
        wishlist: "Wishlist",
        vouchers: "Vouchers",
        supplierPortal: "Supplier portal",
        sellWithUs: "Sell with us",
        logout: "Logout",
        signIn: "Sign in",
      },
      cart: "Cart",
      homeLabel: "Reesolmart home",
      language: { label: "Language", english: "English", swahili: "Kiswahili", french: "Français", arabic: "العربية", hindi: "हिन्दी", mandarin: "简体中文" },
    },
  },
  sw: {
    translation: {
      navigation: { primary: "Kuu", shop: "Nunua" },
      account: {
        greeting: "Habari, {{name}}",
        myAccount: "Akaunti Yangu",
        orders: "Maagizo",
        inbox: "Kikasha",
        wishlist: "Orodha ya Matamanio",
        vouchers: "Vocha",
        supplierPortal: "Tovuti ya msambazaji",
        sellWithUs: "Uza nasi",
        logout: "Ondoka",
        signIn: "Ingia",
      },
      cart: "Kikapu",
      homeLabel: "Ukurasa wa nyumbani wa Reesolmart",
      language: { label: "Lugha", english: "English", swahili: "Kiswahili", french: "Français", arabic: "العربية", hindi: "हिन्दी", mandarin: "简体中文" },
    },
  },
  fr: {
    translation: {
      navigation: { primary: "Principale", shop: "Boutique" },
      account: {
        greeting: "Bonjour, {{name}}",
        myAccount: "Mon compte",
        orders: "Commandes",
        inbox: "Messages",
        wishlist: "Favoris",
        vouchers: "Bons d'achat",
        supplierPortal: "Espace fournisseur",
        sellWithUs: "Vendez avec nous",
        logout: "Déconnexion",
        signIn: "Connexion",
      },
      cart: "Panier",
      homeLabel: "Accueil Reesolmart",
      language: { label: "Langue", english: "English", swahili: "Kiswahili", french: "Français", arabic: "العربية", hindi: "हिन्दी", mandarin: "简体中文" },
    },
  },
  ar: {
    translation: {
      navigation: { primary: "الرئيسية", shop: "تسوّق" },
      account: {
        greeting: "مرحباً، {{name}}",
        myAccount: "حسابي",
        orders: "الطلبات",
        inbox: "الرسائل",
        wishlist: "المفضلة",
        vouchers: "القسائم",
        supplierPortal: "بوابة المورد",
        sellWithUs: "بِع معنا",
        logout: "تسجيل الخروج",
        signIn: "تسجيل الدخول",
      },
      cart: "السلة",
      homeLabel: "الصفحة الرئيسية لريسول مارت",
      language: { label: "اللغة", english: "English", swahili: "Kiswahili", french: "Français", arabic: "العربية", hindi: "हिन्दी", mandarin: "简体中文" },
    },
  },
  hi: {
    translation: {
      navigation: { primary: "मुख्य", shop: "खरीदारी" },
      account: {
        greeting: "नमस्ते, {{name}}",
        myAccount: "मेरा खाता",
        orders: "ऑर्डर",
        inbox: "इनबॉक्स",
        wishlist: "इच्छा-सूची",
        vouchers: "वाउचर",
        supplierPortal: "आपूर्तिकर्ता पोर्टल",
        sellWithUs: "हमारे साथ बेचें",
        logout: "लॉग आउट",
        signIn: "साइन इन",
      },
      cart: "कार्ट",
      homeLabel: "रीसोलमार्ट होम",
      language: { label: "भाषा", english: "English", swahili: "Kiswahili", french: "Français", arabic: "العربية", hindi: "हिन्दी", mandarin: "简体中文" },
    },
  },
  zh: {
    translation: {
      navigation: { primary: "主导航", shop: "购物" },
      account: {
        greeting: "您好，{{name}}",
        myAccount: "我的账户",
        orders: "订单",
        inbox: "收件箱",
        wishlist: "愿望清单",
        vouchers: "优惠券",
        supplierPortal: "供应商门户",
        sellWithUs: "入驻销售",
        logout: "退出登录",
        signIn: "登录",
      },
      cart: "购物车",
      homeLabel: "Reesolmart 首页",
      language: { label: "语言", english: "English", swahili: "Kiswahili", french: "Français", arabic: "العربية", hindi: "हिन्दी", mandarin: "简体中文" },
    },
  },
};

for (const language of supportedLanguages) {
  Object.assign(resources[language].translation, siteResources[language]);
}

function applyDocumentLanguage(language) {
  document.documentElement.lang = language;
  document.documentElement.dir = language === "ar" ? "rtl" : "ltr";
}

i18n.use(initReactI18next).init({
  resources,
  lng: initialLanguage,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

applyDocumentLanguage(initialLanguage);
i18n.on("languageChanged", (language) => {
  localStorage.setItem("reesolmart-language", language);
  applyDocumentLanguage(language);
});

export default i18n;
