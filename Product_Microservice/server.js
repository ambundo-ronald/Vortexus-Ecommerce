const mongoose = require("mongoose");
const dotenv = require("dotenv");

dotenv.config({
    path: ".env",
    quiet: true
})

const app = require("./app");

const PORT = process.env.PORT || 3029;

async function connectDB() {
    try {
        await mongoose.connect(process.env.DATABASE_URL_STRING);

        console.log("Success in connecting to your database");
    } catch (err) {
        console.log("Error in connecting to your database");
    }
}

connectDB();

app.listen(PORT, () => {
    console.log(`Your server has started in port ${PORT}`);
});
