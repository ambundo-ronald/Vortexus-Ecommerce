const mongoose = require('mongoose');
const Product = require('./productModel');

const vesselSchema = new mongoose.Schema({
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
        },
        element_quantity: Number
    },
    specifications: {
        min_flow_rate: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["gpm", "lpm", "m3/h", "gpd"],
                default: "gpm"
            },
            media_type: {
                type: String,
                enum: ["membrane", "carbon", "glass", "sand", "dmi", "resin", "brine", "polypropylene wound/spun/pleated"],
                default: "gpm"
            }
        },
        max_flow_rate: {
            value: {
                type: Number,
            },
            unit: {
                type: String,
                enum: ["gpm", "lpm", "m3/h", "gpd"],
                default: "gpm"
            },
            media_type: {
                type: String,
                enum: ["membrane", "carbon", "glass", "sand", "dmi", "resin", "brine", "polypropylene wound/spun/pleated"],
                default: "gpm"
            }
        },
        inlet: {
            value: {
                type: String,
            },
            unit: {
                type: String,
                enum: ["inch", "cm", "mm", "mtrs"],
                default: "ppm"
            }
        },
        outlet: {
            value: {
                type: String,
            },
            unit: {
                type: String,
                enum: ["inch", "cm", "mm", "mtrs"],
                default: "ppm"
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
        range_temperature: {
            value: {
                type: String,
            },
            unit: {
                type: String,
                enum: ["\({}^{\circ }C\)", "K", "\({}^{\circ }F\)"],
            }
        },
        capacity: {
            value: {
                type: Number
            },
            unit: {
                type: String,
                enum: ["m3", "L"],
            }
        },
        mount: {
            value: {
                type: String
            },
            unit: {
                type: String,
                enum: ["top", "side", "end"]
            }
        },
        details: {
            dimensions: {
                value: {
                    type: String
                },
                unit: {
                    type: String,
                    enum: ['inch', "cm", "m", "mm"],
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
            material: {
                value: {
                    type: String
                },
                unit: {
                    type: String,
                    enum: [
                        "UPVC",
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

const Vessel = Product.discriminator('vessel', vesselSchema)

module.exports = Vessel;
