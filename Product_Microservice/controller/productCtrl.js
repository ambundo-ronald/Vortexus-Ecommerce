const Blower = require("../model/Blower");
const Chemical = require("../model/Chemical");
const Controller = require("../model/Controllers");
const DesalinationSystem = require("../model/DesalinationSystems");
const Filter = require("../model/Filters");
const FlowMeter = require("../model/FlowMeter");
const PlumbingFitting = require("../model/PlumbingFittings");
const Product = require("../model/productModel");
const Sterilizer = require("../model/Sterilizer");
const SubmersiblePump = require("../model/SubmersiblePumps");
const SurfacePump = require("../model/SurfacePumps");
const Vessel = require("../model/Vessels");

const PRODUCT_MODEL_ALIASES = {
    filter: Filter,
    filters: Filter,
    blower: Blower,
    blowers: Blower,
    chemical: Chemical,
    chemicals: Chemical,
    controller: Controller,
    controllers: Controller,
    sterilizer: Sterilizer,
    sterilizers: Sterilizer,
    vessel: Vessel,
    vessels: Vessel,
    surfacepump: SurfacePump,
    surfacepumps: SurfacePump,
    submersiblepump: SubmersiblePump,
    submersiblepumps: SubmersiblePump,
    plumbingfitting: PlumbingFitting,
    plumbingfittings: PlumbingFitting,
    desalinationsystem: DesalinationSystem,
    desalinationsystems: DesalinationSystem,
    flowmeter: FlowMeter,
    flowmeters: FlowMeter,
};

function normalizeProductClass(value = "") {
    return String(value).trim().toLowerCase().replace(/[\s_-]+/g, "");
}

function productModelForCategory(category = "") {
    return PRODUCT_MODEL_ALIASES[normalizeProductClass(category)] || Product;
}

// uploadProductImages, resizeProductImages, updateProduct
/*
 *await sharp("image.jpg")
  .composite([
    {
      input: Buffer.from(`
        <svg width="400" height="50">
          <text x="10" y="35"
                font-size="24"
                fill="white"
                opacity="0.7">
            © Norwa Water
          </text>
        </svg>
      `),
      gravity: "southeast"
    }
  ])
  .toFile("watermarked.jpg");

 import { exiftool } from "exiftool-vendored";

await exiftool.write("image.jpg", {
  Copyright: "© 2026 Norwa Water. All Rights Reserved.",
  Artist: "Norwa Water",
  Creator: "Norwa Water",
  Credit: "Norwa Water",
  UsageTerms: "Unauthorized reproduction prohibited."
});

await exiftool.end();
 * */

exports.getProducts = async (req, res) => {
    try {
        const products = await Product.find({});
        if (products.length < 1) {
            return res.status(200).json({
                status: "success",
                message: "No products added yet",
            })
        }

        res.status(200).json({
            status: "success",
            length: products.length,
            data: {
                products
            }
        })
    } catch (err) {
        res.status(500).json({
            status: "fail",
            message: "There was an error with your request",
            error: err
        })
    }
}

exports.getProduct = async (req, res) => {
    try {
        const product = await Product.findById(req.params.id);

        if (!product) {
            return res.status(404).json({
                status: "fail",
                message: "Product not found"
            })
        }

        res.status(200).json({
            status: 'success',
            data: {
                product
            }
        })
    } catch (err) {
        res.status(500).json({
            status: "fail",
            message: "There was an error with your request",
            error: err
        })
    }
}

exports.createProduct = async (req, res) => {
    try {
        const { category } = req.body;
        const Model = productModelForCategory(category);
        const newProduct = await Model.create(req.body)

        res.status(201).json({
            status: "success",
            data: {
                product: newProduct
            }
        })
    } catch (err) {
        res.status(400).json({
            status: "fail",
            message: err.message || "Invalid product payload"
        })
    }
}

exports.updateProduct = async (req, res) => {
    try {
        const existingProduct = await Product.findById(req.params.id);

        if (!existingProduct) {
            return res.status(404).json({
                status: "fail",
                message: "Product not found"
            })
        }

        const Model = productModelForCategory(req.body.category || existingProduct.category || existingProduct.__t);
        const product = await Model.findByIdAndUpdate(req.params.id, req.body, {
            returnDocument: 'after',
            runValidators: true
        });

        res.status(200).json({
            status: "success",
            data: {
                product
            }
        })
    } catch (err) {
        res.status(400).json({
            status: "fail",
            message: err.message || "Invalid product payload"
        })
    }
}

exports.deleteProduct = async (req, res) => {
    try {
        const product = await Product.findByIdAndDelete(req.params.id);

        if (!product) {
            return res.status(404).json({
                status: "fail",
                message: "Product not found"
            })
        }

        res.status(204).json({
            status: "success",
            data: null
        })
    } catch (err) {
        res.status(500).json({
            status: "fail",
            message: `There was an error with your request ${err}`
        })
    }
}
