DROP TABLE METALS;
CREATE TABLE METALS
(ID SERIAL PRIMARY KEY,
NAME VARCHAR(25));
INSERT INTO METALS (NAME) VALUES ('Aluminium'), ('Cobalt'), ('Copper'), ('Graphite'), ('Gold'), ('Iron'), ('Niobium'), ('Silver'), ('Steel'),('Titanium');
DROP TABLE FLUIDS;
CREATE TABLE FLUIDS
(ID SERIAL PRIMARY KEY,
NAME VARCHAR(25));
INSERT INTO FLUIDS (NAME) VALUES ('Dihydrogen Oxide'), ('Helium'), ('Hydrogen'), ('Oxygen'), ('Tritium'), ('Xenon');
DROP TABLE 
CREATE TABLE "345" (MemberID INT PRIMARY KEY, Credits INT DEFAULT 0, Items VARCHAR(25)[] DEFAULT ARRAY[]::VARCHAR(25)[], Schematics integer[] DEFAULT ARRAY[]::integer[]);
INSERT INTO "345" (MemberID) VALUES (6)