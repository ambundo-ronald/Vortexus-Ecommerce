const mongoose = require('mongoose');
const Product = require('./productModel');

const PlumbingFittingSchema = new mongoose.Schema({
    specifications: {
        plumbing_type: {
            value: {
                type: String,
            },
            unit: {
                type: String,
                enum: ["Auto", "Manual"],
            }
        },
        inlet: {
            value: {
                type: Number
            },
            unit: {
                type: String,
                enum: ['inch', "cm", "m", "mm"],
                default: "inch"
            },
            plumbing: {
                type: String,
                enum: ["female", "male", "flanged"],
            }
        },
        outlet: {
            value: {
                type: Number
            },
            unit: {
                type: String,
                enum: ['inch', "cm", "m", "mm"],
                default: "inch"
            },
            plumbing: {
                type: String,
                enum: ["female", "male", "flanged"],
            }
        },
        drain: {
            value: {
                type: Number
            },
            unit: {
                type: String,
                enum: ['inch', "cm", "m", "mm"],
                default: "inch"
            },
            plumbing: {
                type: String,
                enum: ["female", "male", "flanged"],
            }
        },
        max_pressure_range: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["Pa", "bar", "kPa", "MPa", "psi"],
            }
        },
        electrical_details: {
            voltage: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["V", "Voltage"],
                }
            },
            current: {
                value: String,
                unit: {
                    type: String,
                    enum: ["AC", "DC"],
                }
            },
        },
        range_temperature: {
            value: {
                type: String,
            },
            unit: {
                type: String,
                enum: ["\({}^{\circ }C\)", "K", "\({}^{\circ }F\)"],
            }
        },
        details: {
            dimensions: [String],
            weight: {
                value: {
                    type: Number
                },
                unit: {
                    type: String,
                    enum: ['kg', "g", "mg"],
                }
            },
            material: {
                value: {
                    type: String
                },
                unit: {
                    type: String,
                    enum: [
                        "UPVC",
                        "CPVC",
                        "GI",
                        "HDPE",
                        "stainles steel",
                        "fiber",
                        "glass",
                        "carbon steel",
                    ]
                }
            }
        }
    }
}, {
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
}
)

const PlumbingFitting = Product.discriminator('plumbingfitting', PlumbingFittingSchema)

module.exports = PlumbingFitting;
