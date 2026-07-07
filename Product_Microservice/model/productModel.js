const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
    name: {
        type: String,
        required: [true, 'A product must have a name'],
        unique: true,
        trim: true,
        maxlength: [40, 'A product must have less or equal then 40 char'],
        minlength: [3, 'A product must have more or equal then 3 char'],
    },
    description: {
        type: String,
        required: [true, 'A product must have a description'],
    },
    brand: String,
    category: String,
    sub_category: String,
    application: [String],
    min_price: {
        type: Number,
        max: [999999999999, 'Value cannot exceed 12 digits (999,999,999,999)'],
        min: [0, "Price can't be less than zero"]
    },
    max_price: {
        type: Number,
        max: [999999999999, 'Value cannot exceed 12 digits (999,999,999,999)'],
        min: [0, "Price can't be less than zero"]
    },
    in_stock: Boolean,
    status: {
        type: String,
        enum: ["active", "draft"]
    },
    meta: {
        title: String,
        description: String
    },
    django_product_id: Number,
    django_upc: String
}, {
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
}
)

const Product = mongoose.model('Product', productSchema)

module.exports = Product;
