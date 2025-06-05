CREATE TABLE r4b5i3a9xg3x54bn.SENSOR (
	id INT auto_increment NOT NULL,
	tipo_sensor varchar(100) NULL,
	nome varchar(100) NULL,
	latitude FLOAT NULL,
	logitude varchar(100) NULL,
	status varchar(100) NULL,
	CONSTRAINT Sensor_PK PRIMARY KEY (Id)
)


CREATE TABLE r4b5i3a9xg3x54bn.LEITURAS_SENSORES (
	id INT auto_increment NOT NULL,
	temperatura FLOAT NULL,
	mq2 INT NULL,
	status varchar(100) NULL,
	mensagem varchar(300) NULL,
	id_sensor INT
	CONSTRAINT LEITURAS_SENSORES_PK PRIMARY KEY (id)
)

ALTER TABLE r4b5i3a9xg3x54bn.LEITURA_SENSOR ADD CONSTRAINT LEITURA_SENSOR_SENSOR_FK FOREIGN KEY (id_sensor) REFERENCES r4b5i3a9xg3x54bn.SENSOR(id);
