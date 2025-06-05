const mysql = require("mysql2/promise"); // Importante: use 'mysql2/promise' para async/await

console.log("Criando pool de conexões com o banco de dados...");

const pool = mysql.createPool({
  host: process.env.databaseHost,
  user: process.env.databaseUser,
  password: process.env.databasePassword,
  database: process.env.databaseName,
  port: process.env.databasePort,
  waitForConnections: true, // Espera por uma conexão se o pool estiver cheio
  connectionLimit: 10, // Limite de conexões no pool (ajuste conforme seu plano)
  queueLimit: 0, // Fila de requisições ilimitada
});

module.exports = pool;
