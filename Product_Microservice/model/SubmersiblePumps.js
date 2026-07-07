const mongoose = require('mongoose');
const Product = require('./productModel');

const SubmersiblePumpsSchema = new mongoose.Schema({
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
        fuild_type: {
            value: {
                type: String,
            },
            unit: {
                type: String,
                enum: ["sewage", "borehole", "well/dam", "drainage"],
            }
        },
        max_liquid_temperature: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["\({}^{\circ }C\)", "K", "\({}^{\circ }F\)"],
                default: "\({}^{\circ }C\)"
            }
        },
        min_borehole_diameter: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["mm", "inch"],
                default: "mm"
            }
        },
        max_immersion_diameter: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["mm", "inch"],
                default: "mm"
            }
        },
        details: {
            outlet: {
                value: {
                    type: Number
                },
                unit: {
                    type: String,
                    enum: ['inch', "DN", "m", "mm"],
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
                    enum: ['electrical', "solar"],
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
            current: {
                unit: {
                    type: String,
                    enum: ["AC", "DC"],
                    default: String
                }
            },
            pump_material: {
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
                unit: {
                    type: String,
                    enum: [
                        "copper"
                    ]
                },
                cooled: {
                    type: String,
                    enum: [
                        "water",
                        "oil"
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

const SubmersiblePump = Product.discriminator('SubmersiblePump', SubmersiblePumpsSchema)

module.exports = SubmersiblePump;
