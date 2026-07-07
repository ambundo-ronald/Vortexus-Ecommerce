const mongoose = require('mongoose');
const Product = require('./productModel');

const chemicalSchema = new mongoose.Schema({
    packing_dimensions: {
        weight: {
            value: Number,
            unit: {
                type: String,
                enum: ["kg", "g", "mg"],
            },
        },
        litres: {
            value: Number,
            unit: {
                type: String,
                enum: ["l", "ml"],
            }
        },
    },
    specifications: {
        Regeneration: String,
        Characteristics: [String],
        details: {
            material: {
                value: {
                    type: String
                }
            }
        }
    }
}, {
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
}
)

const Chemical = Product.discriminator('Chemical', chemicalSchema)

module.exports = Chemical;
