const Path = require("path");
const mysql2 = require("mysql2");
const pool = require(Path.join(
  __dirname,
  "..",
  "..",
  "src",
  "db",
  "database.js"
));

exports.databaseSave = async function (req, res) {
  console.log("function databaseSave");
  console.log(req.body);
  // Usando a sintaxe INSERT INTO ... VALUES (...) que é mais padrão
  const sql =
    "INSERT INTO LEITURA_SENSOR (status, mensagem, temperatura, valorMQ2, id_sensor) VALUES (?, ?, ?, ?, ?)";
  const { status, mensagem, temperatura, valorMQ2, id_sensor } = req.body;

  try {
    // pool.query executa a query e libera a conexão de volta para o pool automaticamente
    const [results] = await pool.query(sql, [
      status,
      mensagem,
      temperatura,
      valorMQ2,
      id_sensor,
    ]);
    console.log("Dados inseridos com sucesso! ID:", results.insertId);
    res.status(200).json({
      message: "Dados inseridos com sucesso!",
      insertId: results.insertId,
    });
  } catch (err) {
    console.error("Erro ao inserir dados no banco:", err);
    res
      .status(500)
      .json({ error: "Erro interno do servidor ao salvar os dados." });
  }
};
