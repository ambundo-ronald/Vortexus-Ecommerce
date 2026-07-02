const express = require("express");
const productRoute = require("./routes/productRoute");
const app = express();

app.use(express.json({ limit: '100kb' }))
app.use(express.static(`${__dirname}/public`))

app.use('/api/v1/product', productRoute);
app.use('/api/v1/products', productRoute);

module.exports = app;
