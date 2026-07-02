const mongoose = require('mongoose');
const Product = require('./productModel');

const SterilizerSchema = new mongoose.Schema({
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
        flow_rate: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["g/h", "gpm", "lpm", "m3/h", "gpd"],
            }
        },
        electrical_details: {
            power: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["w", "kW", "MW", "GW"],
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
        max_pressure_range: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["Pa", "bar", "kPa", "MPa", "psi"],
            }
        },
        min_pressure_range: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["Pa", "bar", "kPa", "MPa", "psi"],
                default: "bar"
            }
        },
        service_life: {
            value: {
                type: Number
            },
            unit: {
                type: String,
                enum: ["ltrs", "Days"],
            }
        },
        details: {
            inlet: {
                value: {
                    type: Number
                },
                unit: {
                    type: String,
                    enum: ['inch', "cm", "m", "mm"],
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
                },
                plumbing: {
                    type: String,
                    enum: ["female", "male", "flanged"],
                }
            },
            lamp_quantity: Number,
            lamp_pins: {
                value: {
                    type: String
                },
                unit: {
                    type: String,
                    enum: [
                        "4pin single side",
                        "2pin both sides",
                        "4pin stepped"
                    ]
                }
            },
            lamp_length: {
                value: {
                    type: Number
                },
                unit: {
                    type: String,
                    enum: ['inch', "cm", "m", "mm"],
                },
            }
        }
    }
}, {
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
}
)

const Sterilizer = Product.discriminator('sterilizer', SterilizerSchema)

module.exports = Sterilizer;
