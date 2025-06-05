require("dotenv").config();
let express = require("express");
let bodyParser = require("body-parser");
const cors = require("cors");
let http = require("http");
let path = require("path");
let activity = require("./src/routes/sensors");
const compression = require("compression");

let app = express();

app.use(compression());
app.use(express.json({ limit: "5mb" }));
app.use(express.urlencoded({ limit: "5mb", extended: true }));
app.use(bodyParser.raw({ type: "application/jwt" }));
app.use(bodyParser.json({ limit: "5mb" }));
app.use(bodyParser.urlencoded({ limit: "5mb", extended: true }));
app.use(bodyParser.text({ limit: "5mb" }));
app.set("port", process.env.PORT || 3000);
app.use(cors());

app.post("/fiap/globalSolution", activity.databaseSave);

http.createServer(app).listen(app.get("port"), function () {
  console.log("Express server listening on port " + app.get("port"));
});
