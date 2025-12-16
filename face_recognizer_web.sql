-- Active: 1765531058562@@127.0.0.1@3306@face_recognizer_web
CREATE DATABASE  IF NOT EXISTS `face_recognizer_web`;
USE `face_recognizer_web`;


DROP TABLE IF EXISTS `staff_attendance`;

CREATE TABLE `staff_attendance` (
  `ID` varchar(45) NOT NULL,
  `Date` date NOT NULL DEFAULT (curdate()),
  `CheckIn` time DEFAULT NULL,
  `CheckOut` time DEFAULT NULL,
  PRIMARY KEY (`ID`, `Date`),
  KEY `idx_date` (`Date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `staff_face`;

CREATE TABLE `staff_face` (
  `ID` varchar(20) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Dep` varchar(50) NOT NULL,
  `Encoding` mediumblob,
  PRIMARY KEY (`ID`)
);
DROP TABLE IF EXISTS `student_attendance`;
CREATE TABLE `student_attendance` (
  `ID` varchar(45) NOT NULL,
  `Date` date NOT NULL DEFAULT (curdate()),
  `CheckIn` time DEFAULT NULL,
  PRIMARY KEY (`ID`, `Date`),
  KEY `idx_date` (`Date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

DROP TABLE IF EXISTS `student_face`;
CREATE TABLE `student_face` (
  `ID` varchar(20) NOT NULL,
  `Name` varchar(255) NOT NULL,
  `Course` varchar(50) NOT NULL,
  `Sem` int NOT NULL,
  `Encoding` mediumblob,
  PRIMARY KEY (`ID`)
);
