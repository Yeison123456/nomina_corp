
/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empresa` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `razon_social` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nit` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direccion` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ciudad` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `correo` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `representante_legal` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `actividad_economica` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `exonerada_aportes` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `parametro_legal` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `vigente_desde` date NOT NULL,
  `descripcion` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `smmlv` decimal(14,2) NOT NULL,
  `auxilio_transporte` decimal(14,2) NOT NULL,
  `uvt` decimal(14,2) NOT NULL,
  `horas_mes` smallint unsigned NOT NULL,
  `pct_recargo_nocturno` decimal(6,4) NOT NULL,
  `pct_recargo_dominical` decimal(6,4) NOT NULL,
  `pct_extra_diurna` decimal(6,4) NOT NULL,
  `pct_extra_nocturna` decimal(6,4) NOT NULL,
  `pct_salud_empleado` decimal(6,4) NOT NULL,
  `pct_pension_empleado` decimal(6,4) NOT NULL,
  `pct_salud_empleador` decimal(6,4) NOT NULL,
  `pct_pension_empleador` decimal(6,4) NOT NULL,
  `pct_caja` decimal(6,4) NOT NULL,
  `pct_icbf` decimal(6,4) NOT NULL,
  `pct_sena` decimal(6,4) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `vigente_desde` (`vigente_desde`),
  CONSTRAINT `parametro_legal_chk_1` CHECK ((`horas_mes` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `entidad` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nit` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `codigo` varchar(12) COLLATE utf8mb4_unicode_ci NOT NULL,
  `activa` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `entidad_tipo_nombre_adc8fa52_uniq` (`tipo`,`nombre`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `auditoria` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha` datetime(6) NOT NULL,
  `accion` varchar(40) COLLATE utf8mb4_unicode_ci NOT NULL,
  `objeto` varchar(120) COLLATE utf8mb4_unicode_ci NOT NULL,
  `detalle` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `usuario_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `auditoria_usuario_id_5e766294_fk_auth_user_id` (`usuario_id`),
  CONSTRAINT `auditoria_usuario_id_5e766294_fk_auth_user_id` FOREIGN KEY (`usuario_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `centro_costo` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `codigo` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `area` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `codigo` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `centro_costo_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `area_centro_costo_id_00afb1fd_fk_centro_costo_id` (`centro_costo_id`),
  CONSTRAINT `area_centro_costo_id_00afb1fd_fk_centro_costo_id` FOREIGN KEY (`centro_costo_id`) REFERENCES `centro_costo` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `cargo` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `codigo` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `salario_referencia` decimal(14,2) NOT NULL,
  `area_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  KEY `cargo_area_id_d7efd61f_fk_area_id` (`area_id`),
  CONSTRAINT `cargo_area_id_d7efd61f_fk_area_id` FOREIGN KEY (`area_id`) REFERENCES `area` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `empleado` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tipo_documento` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `numero_documento` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombres` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `apellidos` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_nacimiento` date NOT NULL,
  `genero` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `correo` varchar(254) COLLATE utf8mb4_unicode_ci NOT NULL,
  `telefono` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `direccion` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `ciudad` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo_cuenta` varchar(2) COLLATE utf8mb4_unicode_ci NOT NULL,
  `numero_cuenta` varchar(30) COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL,
  `creado` datetime(6) NOT NULL,
  `actualizado` datetime(6) NOT NULL,
  `afp_id` bigint DEFAULT NULL,
  `banco_id` bigint DEFAULT NULL,
  `caja_id` bigint NOT NULL,
  `eps_id` bigint NOT NULL,
  `fondo_cesantias_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero_documento` (`numero_documento`),
  KEY `empleado_afp_id_906826fb_fk_entidad_id` (`afp_id`),
  KEY `empleado_banco_id_41ac1680_fk_entidad_id` (`banco_id`),
  KEY `empleado_caja_id_c6fdbd5b_fk_entidad_id` (`caja_id`),
  KEY `empleado_eps_id_6cbf2996_fk_entidad_id` (`eps_id`),
  KEY `empleado_fondo_cesantias_id_bb7037c6_fk_entidad_id` (`fondo_cesantias_id`),
  CONSTRAINT `empleado_afp_id_906826fb_fk_entidad_id` FOREIGN KEY (`afp_id`) REFERENCES `entidad` (`id`),
  CONSTRAINT `empleado_banco_id_41ac1680_fk_entidad_id` FOREIGN KEY (`banco_id`) REFERENCES `entidad` (`id`),
  CONSTRAINT `empleado_caja_id_c6fdbd5b_fk_entidad_id` FOREIGN KEY (`caja_id`) REFERENCES `entidad` (`id`),
  CONSTRAINT `empleado_eps_id_6cbf2996_fk_entidad_id` FOREIGN KEY (`eps_id`) REFERENCES `entidad` (`id`),
  CONSTRAINT `empleado_fondo_cesantias_id_bb7037c6_fk_entidad_id` FOREIGN KEY (`fondo_cesantias_id`) REFERENCES `entidad` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contrato` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `numero` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo_salario` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `salario` decimal(14,2) NOT NULL,
  `periodicidad` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `clase_riesgo` smallint unsigned NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date DEFAULT NULL,
  `estado` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_terminacion` date DEFAULT NULL,
  `motivo_terminacion` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `arl_id` bigint NOT NULL,
  `cargo_id` bigint NOT NULL,
  `centro_costo_id` bigint NOT NULL,
  `empleado_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `numero` (`numero`),
  KEY `contrato_arl_id_79f5bed5_fk_entidad_id` (`arl_id`),
  KEY `contrato_cargo_id_49b5786f_fk_cargo_id` (`cargo_id`),
  KEY `contrato_centro_costo_id_67439f90_fk_centro_costo_id` (`centro_costo_id`),
  KEY `contrato_empleado_id_ce355100_fk_empleado_id` (`empleado_id`),
  CONSTRAINT `contrato_arl_id_79f5bed5_fk_entidad_id` FOREIGN KEY (`arl_id`) REFERENCES `entidad` (`id`),
  CONSTRAINT `contrato_cargo_id_49b5786f_fk_cargo_id` FOREIGN KEY (`cargo_id`) REFERENCES `cargo` (`id`),
  CONSTRAINT `contrato_centro_costo_id_67439f90_fk_centro_costo_id` FOREIGN KEY (`centro_costo_id`) REFERENCES `centro_costo` (`id`),
  CONSTRAINT `contrato_empleado_id_ce355100_fk_empleado_id` FOREIGN KEY (`empleado_id`) REFERENCES `empleado` (`id`),
  CONSTRAINT `contrato_chk_1` CHECK ((`clase_riesgo` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `concepto` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `codigo` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL,
  `nombre` varchar(80) COLLATE utf8mb4_unicode_ci NOT NULL,
  `tipo` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `captura` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `salarial` tinyint(1) NOT NULL,
  `base_seguridad_social` tinyint(1) NOT NULL,
  `base_prestaciones` tinyint(1) NOT NULL,
  `base_vacaciones` tinyint(1) NOT NULL,
  `orden` smallint unsigned NOT NULL,
  `descripcion` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `activo` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `codigo` (`codigo`),
  CONSTRAINT `concepto_chk_1` CHECK ((`orden` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=38 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `periodo_nomina` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `periodicidad` varchar(1) COLLATE utf8mb4_unicode_ci NOT NULL,
  `anio` smallint unsigned NOT NULL,
  `mes` smallint unsigned NOT NULL,
  `numero` smallint unsigned NOT NULL,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date NOT NULL,
  `fecha_pago` date NOT NULL,
  `estado` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `observaciones` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_liquidacion` datetime(6) DEFAULT NULL,
  `fecha_cierre` datetime(6) DEFAULT NULL,
  `cerrado_por_id` int DEFAULT NULL,
  `liquidado_por_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `periodo_nomina_periodicidad_anio_mes_numero_3621c26a_uniq` (`periodicidad`,`anio`,`mes`,`numero`),
  KEY `periodo_nomina_cerrado_por_id_85bedb63_fk_auth_user_id` (`cerrado_por_id`),
  KEY `periodo_nomina_liquidado_por_id_1b6856f4_fk_auth_user_id` (`liquidado_por_id`),
  CONSTRAINT `periodo_nomina_cerrado_por_id_85bedb63_fk_auth_user_id` FOREIGN KEY (`cerrado_por_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `periodo_nomina_liquidado_por_id_1b6856f4_fk_auth_user_id` FOREIGN KEY (`liquidado_por_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `periodo_nomina_chk_1` CHECK ((`anio` >= 0)),
  CONSTRAINT `periodo_nomina_chk_2` CHECK ((`mes` >= 0)),
  CONSTRAINT `periodo_nomina_chk_3` CHECK ((`numero` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `novedad` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha_inicio` date NOT NULL,
  `fecha_fin` date DEFAULT NULL,
  `cantidad` decimal(10,2) NOT NULL,
  `valor` decimal(14,2) NOT NULL,
  `observacion` varchar(255) COLLATE utf8mb4_unicode_ci NOT NULL,
  `estado` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creado` datetime(6) NOT NULL,
  `concepto_id` bigint NOT NULL,
  `contrato_id` bigint NOT NULL,
  `registrado_por_id` int DEFAULT NULL,
  `periodo_aplicacion_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `novedad_concepto_id_935c86e4_fk_concepto_id` (`concepto_id`),
  KEY `novedad_contrato_id_c21073f1_fk_contrato_id` (`contrato_id`),
  KEY `novedad_registrado_por_id_99321483_fk_auth_user_id` (`registrado_por_id`),
  KEY `novedad_periodo_aplicacion_id_8d46ce4f_fk_periodo_nomina_id` (`periodo_aplicacion_id`),
  CONSTRAINT `novedad_concepto_id_935c86e4_fk_concepto_id` FOREIGN KEY (`concepto_id`) REFERENCES `concepto` (`id`),
  CONSTRAINT `novedad_contrato_id_c21073f1_fk_contrato_id` FOREIGN KEY (`contrato_id`) REFERENCES `contrato` (`id`),
  CONSTRAINT `novedad_periodo_aplicacion_id_8d46ce4f_fk_periodo_nomina_id` FOREIGN KEY (`periodo_aplicacion_id`) REFERENCES `periodo_nomina` (`id`),
  CONSTRAINT `novedad_registrado_por_id_99321483_fk_auth_user_id` FOREIGN KEY (`registrado_por_id`) REFERENCES `auth_user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=118 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `prestamo` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `descripcion` varchar(150) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha` date NOT NULL,
  `monto` decimal(14,2) NOT NULL,
  `numero_cuotas` smallint unsigned NOT NULL,
  `valor_cuota` decimal(14,2) NOT NULL,
  `saldo` decimal(14,2) NOT NULL,
  `estado` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `creado` datetime(6) NOT NULL,
  `concepto_id` bigint NOT NULL,
  `contrato_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  KEY `prestamo_concepto_id_fba1a854_fk_concepto_id` (`concepto_id`),
  KEY `prestamo_contrato_id_85399e2e_fk_contrato_id` (`contrato_id`),
  CONSTRAINT `prestamo_concepto_id_fba1a854_fk_concepto_id` FOREIGN KEY (`concepto_id`) REFERENCES `concepto` (`id`),
  CONSTRAINT `prestamo_contrato_id_85399e2e_fk_contrato_id` FOREIGN KEY (`contrato_id`) REFERENCES `contrato` (`id`),
  CONSTRAINT `prestamo_chk_1` CHECK ((`numero_cuotas` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `liquidacion_nomina` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `salario` decimal(14,2) NOT NULL,
  `dias_periodo` smallint unsigned NOT NULL,
  `dias_trabajados` smallint unsigned NOT NULL,
  `ibc` decimal(14,2) NOT NULL,
  `base_prestaciones` decimal(14,2) NOT NULL,
  `total_devengado` decimal(14,2) NOT NULL,
  `total_deducciones` decimal(14,2) NOT NULL,
  `neto_pagar` decimal(14,2) NOT NULL,
  `total_aportes` decimal(14,2) NOT NULL,
  `total_provisiones` decimal(14,2) NOT NULL,
  `advertencias` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `creado` datetime(6) NOT NULL,
  `contrato_id` bigint NOT NULL,
  `periodo_id` bigint NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `liquidacion_nomina_periodo_id_contrato_id_0ebb28ad_uniq` (`periodo_id`,`contrato_id`),
  KEY `liquidacion_nomina_contrato_id_bdaf5aa1_fk_contrato_id` (`contrato_id`),
  CONSTRAINT `liquidacion_nomina_contrato_id_bdaf5aa1_fk_contrato_id` FOREIGN KEY (`contrato_id`) REFERENCES `contrato` (`id`),
  CONSTRAINT `liquidacion_nomina_periodo_id_01c9d810_fk_periodo_nomina_id` FOREIGN KEY (`periodo_id`) REFERENCES `periodo_nomina` (`id`),
  CONSTRAINT `liquidacion_nomina_chk_1` CHECK ((`dias_periodo` >= 0)),
  CONSTRAINT `liquidacion_nomina_chk_2` CHECK ((`dias_trabajados` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=97 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `detalle_liquidacion` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `cantidad` decimal(10,2) NOT NULL,
  `base` decimal(14,2) NOT NULL,
  `tasa` decimal(8,5) NOT NULL,
  `valor` decimal(14,2) NOT NULL,
  `concepto_id` bigint NOT NULL,
  `liquidacion_id` bigint NOT NULL,
  `novedad_id` bigint DEFAULT NULL,
  `prestamo_id` bigint DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `detalle_liquidacion_concepto_id_2cf6d97b_fk_concepto_id` (`concepto_id`),
  KEY `detalle_liquidacion_liquidacion_id_345a71be_fk_liquidaci` (`liquidacion_id`),
  KEY `detalle_liquidacion_novedad_id_d1670a64_fk_novedad_id` (`novedad_id`),
  KEY `detalle_liquidacion_prestamo_id_2023b268_fk_prestamo_id` (`prestamo_id`),
  CONSTRAINT `detalle_liquidacion_concepto_id_2cf6d97b_fk_concepto_id` FOREIGN KEY (`concepto_id`) REFERENCES `concepto` (`id`),
  CONSTRAINT `detalle_liquidacion_liquidacion_id_345a71be_fk_liquidaci` FOREIGN KEY (`liquidacion_id`) REFERENCES `liquidacion_nomina` (`id`),
  CONSTRAINT `detalle_liquidacion_novedad_id_d1670a64_fk_novedad_id` FOREIGN KEY (`novedad_id`) REFERENCES `novedad` (`id`),
  CONSTRAINT `detalle_liquidacion_prestamo_id_2023b268_fk_prestamo_id` FOREIGN KEY (`prestamo_id`) REFERENCES `prestamo` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=1176 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `liquidacion_contrato` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `fecha_retiro` date NOT NULL,
  `causa` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `salario` decimal(14,2) NOT NULL,
  `auxilio_transporte` decimal(14,2) NOT NULL,
  `promedio_variable` decimal(14,2) NOT NULL,
  `dias_cesantias` int unsigned NOT NULL,
  `base_cesantias` decimal(14,2) NOT NULL,
  `cesantias` decimal(14,2) NOT NULL,
  `intereses_cesantias` decimal(14,2) NOT NULL,
  `dias_prima` int unsigned NOT NULL,
  `prima` decimal(14,2) NOT NULL,
  `dias_vacaciones` decimal(8,2) NOT NULL,
  `vacaciones` decimal(14,2) NOT NULL,
  `indemnizacion` decimal(14,2) NOT NULL,
  `total` decimal(14,2) NOT NULL,
  `estado` varchar(3) COLLATE utf8mb4_unicode_ci NOT NULL,
  `observaciones` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `fecha_elaboracion` datetime(6) NOT NULL,
  `contrato_id` bigint NOT NULL,
  `elaborado_por_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `contrato_id` (`contrato_id`),
  KEY `liquidacion_contrato_elaborado_por_id_3c00087f_fk_auth_user_id` (`elaborado_por_id`),
  CONSTRAINT `liquidacion_contrato_contrato_id_88dee505_fk_contrato_id` FOREIGN KEY (`contrato_id`) REFERENCES `contrato` (`id`),
  CONSTRAINT `liquidacion_contrato_elaborado_por_id_3c00087f_fk_auth_user_id` FOREIGN KEY (`elaborado_por_id`) REFERENCES `auth_user` (`id`),
  CONSTRAINT `liquidacion_contrato_chk_1` CHECK ((`dias_cesantias` >= 0)),
  CONSTRAINT `liquidacion_contrato_chk_2` CHECK ((`dias_prima` >= 0))
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

