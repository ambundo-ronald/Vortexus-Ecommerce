const express = require("express");
const { getProducts, getProduct, createProduct, updateProduct, deleteProduct } = require("../controller/productCtrl");

const route = express.Router();

route.get("/", getProducts);
route.post("/", createProduct);
route.get("/:id", getProduct);
route.patch("/:id", updateProduct);
route.delete("/:id", deleteProduct);

// route.patch("/:id", uploadProductImages, resizeProductImages, updateProduct);

module.exports = route;
