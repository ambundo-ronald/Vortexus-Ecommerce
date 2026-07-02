const mongoose = require('mongoose');
const Product = require('./productModel');

const SurfacePumpsSchema = new mongoose.Schema({
    packing_dimensions: {
        length: {
            value: Number,
            unit: {
                type: String,
                enum: ["mm", "cm", "m"],
                default: "cm"
            }
        },
        width: {
            value: Number,
            unit: {
                type: String,
                enum: ["mm", "cm", "m"],
                default: "cm"
            }
        },
        height: {
            value: Number,
            unit: {
                type: String,
                enum: ["mm", "cm", "m"],
                default: "cm"
            }
        },
        weight: {
            value: Number,
            unit: {
                type: String,
                enum: ["kg", "g", "mg"],
                default: "g"
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
                default: "gpm"
            }
        },
        min_flow_rate: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["gpm", "lpm", "m3/h", "gpd"],
                default: "gpm"
            }
        },
        electrical_details: {
            power: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["w", "kW", "MW", "GW"],
                    default: "w"
                }
            },
            horse_power: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["hp", "w", "ahp"],
                    default: "hp"
                }
            },
            voltage: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["V", "Voltage"],
                    default: "V"
                }
            },
            ampere: {
                value: Number,
                unit: {
                    type: String,
                    enum: ["V", "Voltage"],
                    default: "V"
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
                default: "bar"
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
        pump_type: {
            value: {
                type: String,
            },
            unit: {
                type: String,
                enum: [
                    "Vertical Multistage Centrifugal",
                    "Horizontal Multistage Centrifugal",
                    "Domestic",
                    "Domestic silence",
                    "Circulator",
                    "Sanitary",
                    "Dosing"
                ],
            }
        },
        speed: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["rpm", "m/s", "km/h"],
                default: "rpm"
            }
        },
        liquid_temperature: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["\({}^{\circ }C\)", "K", "\({}^{\circ }F\)"],
                default: "\({}^{\circ }C\)"
            }
        },
        max_suction_lift: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["Pa", "bar", "kPa", "m"],
                default: "m"
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
                    default: "inch"
                },
                plumbing: {
                    type: String,
                    enum: ["female", "male", "flanged"],
                    default: "female"
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
                    default: "female"
                }
            },
            weight: {
                value: {
                    type: Number
                },
                unit: {
                    type: String,
                    enum: ['kg', "g", "mg"],
                    default: "g"
                }
            },
            pumped_liquids: String,
            energy: {
                unit: {
                    type: String,
                    enum: ["electrical", "solar", "petrol", "diesel"],
                    default: "electrical"
                }
            },
            phase: {
                unit: {
                    type: Number,
                    enum: [1, 3],
                    default: 1
                }
            },
            pump_material: {
                value: {
                    type: String
                },
                unit: {
                    type: String,
                    enum: [
                        "plastic",
                        "GI",
                        "ss",
                        "ss304",
                        "ss316"
                    ]
                }
            },
            motor_material: {
                value: {
                    type: String
                },
                unit: {
                    type: String,
                    enum: [
                        "plastic",
                        "GI",
                        "ss",
                        "ss304",
                        "ss316"
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

const SurfacePump = Product.discriminator('SurfacePump', SurfacePumpsSchema)

module.exports = SurfacePump;
