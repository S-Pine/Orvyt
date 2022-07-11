CREATE TABLE METALS
(ID SERIAL PRIMARY KEY,
NAME VARCHAR(25));
INSERT INTO METALS (NAME) VALUES ('Aluminium'), ('Cobalt'), ('Copper'), ('Graphite'), ('Gold'), ('Iron'), ('Niobium'), ('Silver'), ('Steel'),('Titanium');
CREATE TABLE FLUIDS
(ID SERIAL PRIMARY KEY,
NAME VARCHAR(25));
INSERT INTO FLUIDS (NAME) VALUES ('Dihydrogen Oxide'), ('Helium'), ('Hydrogen'), ('Oxygen'), ('Tritium'), ('Xenon');
