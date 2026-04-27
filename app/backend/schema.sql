SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;
SET UNIQUE_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';

DROP TABLE IF EXISTS `inventariomesdetalle`;
DROP TABLE IF EXISTS `inventariomes`;
DROP TABLE IF EXISTS `producto`;
DROP TABLE IF EXISTS `productotalos`;
DROP TABLE IF EXISTS `almacen`;
DROP TABLE IF EXISTS `categoria`;
DROP TABLE IF EXISTS `unidadmedida`;

CREATE TABLE `unidadmedida` (
  `idunidadmedida` int NOT NULL AUTO_INCREMENT,
  `unidadmedida_nombre` varchar(255) NOT NULL,
  `unidadmedida_es_MX` varchar(255) NOT NULL DEFAULT '',
  `unidadmedida_en_US` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`idunidadmedida`),
  KEY `unidadmedida_nombre_idx` (`unidadmedida_nombre`),
  KEY `unidadmedida_en_US_idx` (`unidadmedida_en_US`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb3;

CREATE TABLE `categoria` (
  `idcategoria` int NOT NULL AUTO_INCREMENT,
  `categoria_nombre` varchar(255) NOT NULL,
  `idcategoriapadre` int DEFAULT NULL,
  `categoria_almacenable` tinyint(1) DEFAULT NULL COMMENT 'sólo aplica para las subcategorias',
  `categoria_visiblecierre` tinyint DEFAULT '1',
  `idcategoriagrupo` int unsigned DEFAULT NULL,
  PRIMARY KEY (`idcategoria`),
  KEY `idcategoriapadre` (`idcategoriapadre`),
  KEY `categoria_almacenable_idx` (`categoria_almacenable`),
  KEY `categoria_visiblecierre_idx` (`categoria_visiblecierre`),
  KEY `idx_idcategoriagrupo` (`idcategoriagrupo`),
  CONSTRAINT `idcategoriapadre_categoria`
    FOREIGN KEY (`idcategoriapadre`) REFERENCES `categoria` (`idcategoria`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=354 DEFAULT CHARSET=utf8mb3;

CREATE TABLE `almacen` (
  `idalmacen` int NOT NULL AUTO_INCREMENT,
  `idsucursal` int NOT NULL,
  `almacen_nombre` varchar(255) NOT NULL,
  `almacen_encargado` varchar(255) DEFAULT 'x',
  `almacen_estatus` tinyint(1) NOT NULL,
  `almacen_oculto` tinyint(1) NOT NULL DEFAULT '0',
  `almacen_usuarios` text,
  `almaen_oculto` int DEFAULT '0',
  `almacen_fechacreacion` date DEFAULT NULL,
  PRIMARY KEY (`idalmacen`),
  KEY `idsucursal` (`idsucursal`),
  KEY `almacen_nombre_idx` (`almacen_nombre`),
  KEY `almacen_estatus_idx` (`almacen_estatus`)
) ENGINE=InnoDB AUTO_INCREMENT=18425 DEFAULT CHARSET=utf8mb3;

CREATE TABLE `productotalos` (
  `idproductotalos` int NOT NULL AUTO_INCREMENT,
  `producto_nombre` text NOT NULL,
  `idunidadmedida` int NOT NULL,
  `idcategoria` int DEFAULT NULL,
  `idsubcategoria` int DEFAULT NULL,
  `producto_rendimiento` decimal(15,6) DEFAULT '0.000000' COMMENT 'sólo aplica cuando es de la categoría bebidas, ',
  `producto_rendimientooriginal` decimal(15,6) DEFAULT '0.000000',
  `division_clave` varchar(255) DEFAULT NULL,
  `grupo_clave` varchar(255) DEFAULT NULL,
  `clase_clave` varchar(255) DEFAULT NULL,
  `subclase_clave` varchar(255) DEFAULT NULL,
  `producto_validado` tinyint DEFAULT '0',
  `total` int DEFAULT '0',
  `producto_visible` tinyint DEFAULT '0',
  PRIMARY KEY (`idproductotalos`),
  KEY `idunidadmedida` (`idunidadmedida`),
  KEY `idsubcategoria` (`idsubcategoria`),
  KEY `idcategoria` (`idcategoria`),
  KEY `producto_validado_idx` (`producto_validado`),
  CONSTRAINT `idcategoria_productotalos`
    FOREIGN KEY (`idcategoria`) REFERENCES `categoria` (`idcategoria`),
  CONSTRAINT `idsubcategoria_productotalos`
    FOREIGN KEY (`idsubcategoria`) REFERENCES `categoria` (`idcategoria`),
  CONSTRAINT `idunidadmedida_productotalos`
    FOREIGN KEY (`idunidadmedida`) REFERENCES `unidadmedida` (`idunidadmedida`)
) ENGINE=InnoDB AUTO_INCREMENT=3050 DEFAULT CHARSET=utf8mb3;

CREATE TABLE `producto` (
  `idproducto` int NOT NULL AUTO_INCREMENT,
  `id_aersa` varchar(255) DEFAULT NULL,
  `idempresa` int NOT NULL,
  `idunidadmedida` int NOT NULL,
  `idimpuesto` int unsigned DEFAULT NULL,
  `producto_nombre` varchar(255) NOT NULL,
  `idcategoria` int DEFAULT NULL,
  `idsubcategoria` int DEFAULT NULL,
  `producto_rendimiento` decimal(15,6) NOT NULL DEFAULT '1.000000' COMMENT 'sólo aplica cuando es de la categoría bebidas, ',
  `producto_ultimocosto` decimal(15,2) DEFAULT '0.00',
  `producto_baja` tinyint(1) NOT NULL DEFAULT '0',
  `producto_tipo` enum('simple','subreceta','plu') NOT NULL,
  `producto_costo` decimal(15,2) DEFAULT '0.00',
  `producto_iva` tinyint(1) DEFAULT '0',
  `producto_precio` decimal(15,2) DEFAULT '0.00',
  `producto_rendimientooriginal` decimal(15,6) DEFAULT '0.000000',
  `producto_ieps` decimal(15,2) DEFAULT '0.00',
  `producto_oculto` tinyint NOT NULL DEFAULT '0',
  `producto_preciofranquicia` decimal(15,2) DEFAULT '0.00',
  `producto_comentarioreceta` text,
  `division_clave` varchar(255) DEFAULT NULL,
  `grupo_clave` varchar(255) DEFAULT NULL,
  `clase_clave` varchar(255) DEFAULT NULL,
  `subclase_clave` varchar(255) DEFAULT NULL,
  `producto_costomaximo` double(15,2) DEFAULT NULL,
  `producto_disponiblemarket` tinyint NOT NULL DEFAULT '0',
  `producto_descripcion` varchar(255) DEFAULT NULL,
  `idproductotalos` int DEFAULT NULL,
  `productotalos_validado` tinyint DEFAULT '0',
  `image_path` varchar(255) DEFAULT NULL,
  `created_at` datetime DEFAULT NULL,
  PRIMARY KEY (`idproducto`),
  KEY `idunidadmedida` (`idunidadmedida`),
  KEY `idempresa` (`idempresa`),
  KEY `idsubcategoria` (`idsubcategoria`),
  KEY `idcategoria` (`idcategoria`),
  KEY `idimpuesto` (`idimpuesto`),
  KEY `idproductotalos` (`idproductotalos`),
  KEY `producto_nombre_idx` (`producto_nombre`),
  KEY `producto_baja_idx` (`producto_baja`),
  KEY `producto_tipo_idx` (`producto_tipo`),
  KEY `producto_oculto_idx` (`producto_oculto`),
  CONSTRAINT `idcategoria_producto`
    FOREIGN KEY (`idcategoria`) REFERENCES `categoria` (`idcategoria`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `idsubcategoria_producto`
    FOREIGN KEY (`idsubcategoria`) REFERENCES `categoria` (`idcategoria`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `idunidadmedida_producto`
    FOREIGN KEY (`idunidadmedida`) REFERENCES `unidadmedida` (`idunidadmedida`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=359164 DEFAULT CHARSET=utf8mb3;

CREATE TABLE `inventariomes` (
  `idinventariomes` int NOT NULL AUTO_INCREMENT,
  `idempresa` int NOT NULL,
  `idsucursal` int NOT NULL,
  `idalmacen` int NOT NULL,
  `idusuario` int NOT NULL COMMENT 'empleado de la empresa quien realizó el registro del inventario\n',
  `idauditor` int DEFAULT NULL COMMENT 'empleado de aersa quien revisará el registro\n',
  `idpadre` int DEFAULT NULL,
  `inventariomes_fecha` datetime NOT NULL,
  `inventariomes_revisada` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'por defecto, el registro se pone como no revisado. \nsi se define como revisada, ya no se podrán modificar los registros del inventario',
  `inventariomes_finalalimentos` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT 'sumatoria de todos los elementos de inventariomesdetalle_importefisico de los productos de la categoria alimentos',
  `inventariomes_finalbebidas` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT 'sumatoria de todos los elementos de inventariomesdetalle_importefisico de los productos de la categoria bebidas',
  `inventariomes_faltantes` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT 'sumatoria de la columna inventariomesdetalle cuando es negativo',
  `inventariomes_sobrantes` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT 'sumatoria de la columna inventariomesdetalle cuando es mayor que 0',
  `inventariomes_total` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT 'sumatoria de faltantes y sobrantes',
  `inventariomes_totalimportefisico` decimal(15,2) NOT NULL DEFAULT '0.00' COMMENT 'sumatoria de inventariomesdetalle_importefisico\\n\\n',
  `inventariomes_estatus` enum('generando','finalizado','error','editando','aplicado','terminado') NOT NULL DEFAULT 'finalizado',
  `inventariomes_finalmiscelaneos` decimal(15,2) DEFAULT '0.00',
  `inventariomes_xls` text,
  `inventariomes_pdf` text,
  `inventariomes_xls_inicial` text,
  `inventariomes_pdf_inicial` text,
  `inventariomes_version` int NOT NULL DEFAULT '1',
  `inventariomes_createdat` datetime DEFAULT NULL,
  `inventariomes_updatedat` datetime DEFAULT NULL,
  PRIMARY KEY (`idinventariomes`),
  KEY `idauditor` (`idauditor`),
  KEY `idempresa` (`idempresa`),
  KEY `idsucursal` (`idsucursal`),
  KEY `idalmacen` (`idalmacen`),
  KEY `idusuario` (`idusuario`),
  KEY `idpadre` (`idpadre`),
  KEY `inventariomes_estatus` (`inventariomes_estatus`),
  KEY `inventariomes_fecha` (`inventariomes_fecha`),
  KEY `idx_inventariomes_emp_suc_fec` (`idempresa`,`idsucursal`,`inventariomes_fecha`),
  CONSTRAINT `idalmacen_inventariomes`
    FOREIGN KEY (`idalmacen`) REFERENCES `almacen` (`idalmacen`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `idpadre_inventariomes`
    FOREIGN KEY (`idpadre`) REFERENCES `inventariomes` (`idinventariomes`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=118906 DEFAULT CHARSET=utf8mb3;

CREATE TABLE `inventariomesdetalle` (
  `idinventariomesdetalle` int NOT NULL AUTO_INCREMENT,
  `idinventariomes` int NOT NULL,
  `idproducto` int NOT NULL,
  `inventariomesdetalle_stockinicial` decimal(15,6) NOT NULL DEFAULT '0.000000',
  `inventariomesdetalle_stockteorico` decimal(15,6) NOT NULL DEFAULT '0.000000',
  `inventariomesdetalle_explosion` decimal(15,6) NOT NULL DEFAULT '0.000000' COMMENT 'este campo contiene las cantidades después de explosionar una receta\\n\\n',
  `inventariomesdetalle_stockfisico` decimal(15,3) DEFAULT '0.000',
  `inventariomesdetalle_totalfisico` decimal(15,6) NOT NULL DEFAULT '0.000000' COMMENT 'es un campo automático, es la sumatoria de stock fisico y explosion.\\n\\ncampo deshabilitado para edición\\n\\nal momento de cambiar el input de stock fisico, este campo se debe de actualizar',
  `inventariomesdetalle_diferencia` decimal(15,6) DEFAULT '0.000000' COMMENT 'diferencia entre el stock teorico y el fisico',
  `inventariomesdetalle_revisada` tinyint(1) NOT NULL DEFAULT '0' COMMENT 'por defecto, se pone como no revisada.\nSi el registro se pone como revisado, ya no se podrá modificar la existencia. ',
  `inventariomesdetalle_ingresocompra` decimal(15,6) NOT NULL DEFAULT '0.000000',
  `inventariomesdetalle_ingresorequisicion` decimal(15,6) NOT NULL DEFAULT '0.000000',
  `inventariomesdetalle_egresorequisicion` decimal(15,6) NOT NULL DEFAULT '0.000000',
  `inventariomesdetalle_egresoventa` decimal(15,6) NOT NULL DEFAULT '0.000000',
  `inventariomesdetalle_reajuste` decimal(15,6) NOT NULL DEFAULT '0.000000' COMMENT 'campo para setear los reajustes del producto.',
  `inventariomesdetalle_ingresoordentablajeria` decimal(15,6) NOT NULL DEFAULT '0.000000',
  `inventariomesdetalle_egresoordentablajeria` decimal(15,6) DEFAULT '0.000000',
  `inventariomesdetalle_egresodevolucion` decimal(15,6) DEFAULT '0.000000',
  `inventariomesdetalle_costopromedio` decimal(15,2) DEFAULT '0.00',
  `inventariomesdetalle_difimporte` decimal(15,2) DEFAULT '0.00' COMMENT 'multiplicacion de la diferencia por el costo promedio',
  `inventariomesdetalle_importefisico` decimal(15,2) DEFAULT '0.00' COMMENT 'multiplicacion del stock fisico por el costo promedio',
  `inventariomesdetalle_aclaracion` text,
  `inventariomesdetalle_categoria_aclaracion` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`idinventariomesdetalle`),
  KEY `idinventariomes` (`idinventariomes`),
  KEY `idproducto_inventariomesdetalle` (`idproducto`),
  KEY `idx_inventariomesdet_inv_pro` (`idinventariomes`,`idproducto`),
  CONSTRAINT `idinventariomes_inventariomesdetalle`
    FOREIGN KEY (`idinventariomes`) REFERENCES `inventariomes` (`idinventariomes`)
    ON DELETE CASCADE ON UPDATE CASCADE,
  CONSTRAINT `idproducto_inventariomesdetalle`
    FOREIGN KEY (`idproducto`) REFERENCES `producto` (`idproducto`)
    ON DELETE CASCADE ON UPDATE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=97517414 DEFAULT CHARSET=utf8mb3;

SET UNIQUE_CHECKS = 1;
SET FOREIGN_KEY_CHECKS = 1;