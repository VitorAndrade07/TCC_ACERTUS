-- MySQL dump 10.13  Distrib 8.0.34, for Win64 (x86_64)
--
-- Host: localhost    Database: acertus_db
-- ------------------------------------------------------
-- Server version	8.0.44

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `answers`
--

DROP TABLE IF EXISTS `answers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `answers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `response_id` int NOT NULL,
  `question_id` int NOT NULL,
  `answer_text` text,
  `option_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `response_id` (`response_id`),
  KEY `question_id` (`question_id`),
  KEY `option_id` (`option_id`),
  CONSTRAINT `answers_ibfk_1` FOREIGN KEY (`response_id`) REFERENCES `responses` (`id`) ON DELETE CASCADE,
  CONSTRAINT `answers_ibfk_2` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE,
  CONSTRAINT `answers_ibfk_3` FOREIGN KEY (`option_id`) REFERENCES `question_options` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `answers`
--

LOCK TABLES `answers` WRITE;
/*!40000 ALTER TABLE `answers` DISABLE KEYS */;
INSERT INTO `answers` VALUES (1,1,1,'matheus legal',NULL),(2,1,2,NULL,1),(3,1,3,NULL,2),(4,2,4,'o joao é legal',NULL),(5,2,5,'joao marcos e edgard',NULL),(6,2,6,NULL,3),(7,2,7,NULL,4);
/*!40000 ALTER TABLE `answers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `forms`
--

DROP TABLE IF EXISTS `forms`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `forms` (
  `id` int NOT NULL AUTO_INCREMENT,
  `user_id` int NOT NULL,
  `title` varchar(255) NOT NULL,
  `description` text,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `forms_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=16 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `forms`
--

LOCK TABLES `forms` WRITE;
/*!40000 ALTER TABLE `forms` DISABLE KEYS */;
INSERT INTO `forms` VALUES (1,1,'Satifacao','','2025-11-03 12:02:29'),(2,2,'Pesquisa de Satisfação','','2025-11-03 12:17:56'),(10,4,'OIOI','EU gosto de peixxe','2025-11-18 16:57:17'),(11,4,'oioi','','2025-11-18 16:58:35'),(12,4,'OIOI','','2025-11-18 17:32:14'),(13,4,'OIOI','','2025-11-18 17:32:18'),(14,4,'TESTE','','2025-11-18 17:34:36'),(15,3,'Olá','Formulário','2025-11-18 17:37:22');
/*!40000 ALTER TABLE `forms` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `question_options`
--

DROP TABLE IF EXISTS `question_options`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `question_options` (
  `id` int NOT NULL AUTO_INCREMENT,
  `question_id` int NOT NULL,
  `option_text` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `question_id` (`question_id`),
  CONSTRAINT `question_options_ibfk_1` FOREIGN KEY (`question_id`) REFERENCES `questions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `question_options`
--

LOCK TABLES `question_options` WRITE;
/*!40000 ALTER TABLE `question_options` DISABLE KEYS */;
INSERT INTO `question_options` VALUES (1,2,'Opção Padrão 1'),(2,3,'Opção Padrão 1'),(3,6,'Opção Padrão 1'),(4,7,'Opção Padrão 1'),(16,20,'Opção Padrão 1'),(17,20,'Nova Opção'),(20,22,'Opção Padrão 1'),(21,22,'Nova Opção'),(22,23,'Opção Padrão 1'),(23,23,'Nova Opção');
/*!40000 ALTER TABLE `question_options` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `questions`
--

DROP TABLE IF EXISTS `questions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `questions` (
  `id` int NOT NULL AUTO_INCREMENT,
  `form_id` int NOT NULL,
  `question_text` text NOT NULL,
  `question_type` enum('text','multiple_choice','checkbox') DEFAULT 'text',
  `order_index` int NOT NULL DEFAULT '0',
  `is_required` tinyint(1) NOT NULL DEFAULT '0',
  PRIMARY KEY (`id`),
  KEY `form_id` (`form_id`),
  CONSTRAINT `questions_ibfk_1` FOREIGN KEY (`form_id`) REFERENCES `forms` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=24 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `questions`
--

LOCK TABLES `questions` WRITE;
/*!40000 ALTER TABLE `questions` DISABLE KEYS */;
INSERT INTO `questions` VALUES (1,1,'Nova Pergunta de Text','text',1,0),(2,1,'Nova Pergunta de Multiple Choice','multiple_choice',2,0),(3,1,'Nova Pergunta de Checkbox','checkbox',3,0),(4,2,'Nova Pergunta de Text','text',1,0),(5,2,'Nova Pergunta de Text','text',2,0),(6,2,'Nova Pergunta de Multiple Choice','multiple_choice',3,0),(7,2,'Nova Pergunta de Checkbox','checkbox',4,0),(15,11,'Nova Pergunta de Text','text',1,0),(16,13,'OIOI','text',1,0),(17,13,'Nova Pergunta de Text','text',2,0),(18,13,'Nova Pergunta de Text','text',3,0),(19,14,'OIOI','text',1,0),(20,14,'OIOI','multiple_choice',2,0),(21,15,'Nova Pergunta de Text','text',1,0),(22,15,'Nova Pergunta de Multiple Choice','multiple_choice',2,0),(23,15,'Nova Pergunta de Checkbox','checkbox',3,0);
/*!40000 ALTER TABLE `questions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `responses`
--

DROP TABLE IF EXISTS `responses`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `responses` (
  `id` int NOT NULL AUTO_INCREMENT,
  `form_id` int NOT NULL,
  `user_id` int DEFAULT NULL,
  `submitted_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `form_id` (`form_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `responses_ibfk_1` FOREIGN KEY (`form_id`) REFERENCES `forms` (`id`) ON DELETE CASCADE,
  CONSTRAINT `responses_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `responses`
--

LOCK TABLES `responses` WRITE;
/*!40000 ALTER TABLE `responses` DISABLE KEYS */;
INSERT INTO `responses` VALUES (1,1,1,'2025-11-03 12:02:54'),(2,2,2,'2025-11-03 12:19:01');
/*!40000 ALTER TABLE `responses` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `users`
--

DROP TABLE IF EXISTS `users`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password` varchar(255) NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `users`
--

LOCK TABLES `users` WRITE;
/*!40000 ALTER TABLE `users` DISABLE KEYS */;
INSERT INTO `users` VALUES (1,'Luiz Felipe','luiz@gmail.com','scrypt:32768:8:1$TEWpLnJuNy7LfOOH$a2ac996ef95d64e461e1a744c433620a0ece0a67528e69db30a522475a6ab92918d0996f6c4bee37caa816ec849f92b0739afc9a973bfee1e90d1292ba792cad','2025-11-03 12:02:07'),(2,'João Marcos','joao@gmail.com','scrypt:32768:8:1$d2SDVZI1RFwS4xsN$cda33ba3e55f370bc5bd0df2b1528b219c8c19611aa77e920bf21376912cd9fcfaa41ed5aacb635a017821d4a1a8b6f2248f382f2bfdabec080caae09b190b3e','2025-11-03 12:17:10'),(3,'Matheus ','sakiiicn@gmail.com','scrypt:32768:8:1$8lc4P6yQLDXHzfHr$4694b5e806aeca982c73bbc3df520b60291f8285099de63bd933ae198dc42634844e4bc488576e36f3db358917d7df3533a27dfa73b243fc2da340425468eaf9','2025-11-10 18:44:59'),(4,'Matheus','matheuscarrasconunes@gmail.com','scrypt:32768:8:1$viKW0owuA6ftqDX6$56c5b443d30b272e99e30e3ee31f15e1f41badf6fd1f0c84a14f699c5dd4d8979b322a8d08eca3a6cf3fe01cd4d3c452f9a7bb47fd06a4ca9592f6327f7bd24c','2025-11-18 14:09:34');
/*!40000 ALTER TABLE `users` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'acertus_db'
--

--
-- Dumping routines for database 'acertus_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-11-24 15:26:03
