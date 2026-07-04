const mongoose = require('mongoose');
const Product = require('./productModel');

const ControllerSchema = new mongoose.Schema({
    packing_dimensions: {
        length: {
            value: Number,
            unit: {
                type: String,
                enum: ["mm", "cm", "m"],
            }
        },
        width: {
            value: Number,
            unit: {
                type: String,
                enum: ["mm", "cm", "m"],
            }
        },
        height: {
            value: Number,
            unit: {
                type: String,
                enum: ["mm", "cm", "m"],
            }
        },
        weight: {
            value: Number,
            unit: {
                type: String,
                enum: ["kg", "g", "mg"],
            },
        }
    },
    specifications: {
        sensor_type: String,
        electrical_details: {
            power: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["w", "kW", "MW", "GW"],
                    default: "w"
                }
            },
            voltage: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["V", "Voltage"],
                }
            },
            ampere: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["V", "Voltage"],
                }
            },
        },
        output_reading: [String],
        display_details: {
            length: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["mm", "cm", "m"],
                }
            },
            width: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["mm", "cm", "m"],
                }
            },
            height: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["mm", "cm", "m"],
                }
            }
        }
    }
}, {
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
}
)

const Controller = Product.discriminator('controller', ControllerSchema)

module.exports = Controller;
