const mongoose = require('mongoose');
const Product = require('./productModel');

const DesalinationSystemSchema = new mongoose.Schema({
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
        max_flow_rate: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["gpm", "lpm", "m3/h", "gpd"],
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
            horse_power: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["hp", "w", "ahp"],
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
            }
        },
        salt_rejection: String,
        details: {
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
            elements: {
                value: {
                    type: Number
                },
                stages: {
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

const DesalinationSystem = Product.discriminator('desalinationsystem', DesalinationSystemSchema)

module.exports = DesalinationSystem;
