"""Writes answers_stage5.json: Claude's hand-written replies to the five stage 5 prompts."""
import json

def ent(name, typ, desc, conf, src):
    return f"<entity>\n<name>{name}</name>\n<type>{typ}</type>\n<description>{desc}</description>\n<confidence>{conf}</confidence>\n<source_text>{src}</source_text>\n</entity>"
def rel(s, t, typ, desc, strength, src):
    return f"<relationship>\n<source>{s}</source>\n<target>{t}</target>\n<type>{typ}</type>\n<description>{desc}</description>\n<strength>{strength}</strength>\n<source_text>{src}</source_text>\n</relationship>"
def reply(ents, rels):
    return "<entities>\n" + "\n".join(ents) + "\n</entities>\n\n<relationships>\n" + "\n".join(rels) + "\n</relationships>"

A = {}
# 01_acme.txt
A["481b2e4f4b"] = reply([
    ent("Acme Robotics", "ORGANIZATION", "A company based in Pune that builds warehouse robots and has 120 employees.", 10, "Acme Robotics is a company based in Pune."),
    ent("Pune", "LOCATION", "The city where Acme Robotics is based.", 10, "Acme Robotics is a company based in Pune."),
    ent("Meera Shah", "PERSON", "The founder of Acme Robotics.", 10, "It was founded by Meera Shah in 2015."),
    ent("2015", "TEMPORAL", "The year Acme Robotics was founded.", 9, "It was founded by Meera Shah in 2015."),
    ent("warehouse robots", "OBJECT", "The products Acme Robotics builds.", 8, "Acme builds warehouse robots."),
], [
    rel("Acme Robotics", "Pune", "LOCATED_IN", "Acme Robotics is based in Pune.", 9, "Acme Robotics is a company based in Pune."),
    rel("Meera Shah", "Acme Robotics", "FOUNDED", "Meera Shah founded Acme Robotics in 2015.", 10, "It was founded by Meera Shah in 2015."),
    rel("Acme Robotics", "warehouse robots", "CREATES", "Acme Robotics builds warehouse robots.", 9, "Acme builds warehouse robots."),
])
# 03_orbit.txt
A["47fccd1fd4"] = reply([
    ent("Orbit Logistics", "ORGANIZATION", "A company that runs warehouses in Mumbai and Chennai and signed a supply contract with Acme Robotics in 2022.", 10, "Orbit Logistics runs warehouses in Mumbai and Chennai."),
    ent("Mumbai", "LOCATION", "A city where Orbit Logistics runs warehouses.", 10, "Orbit Logistics runs warehouses in Mumbai and Chennai."),
    ent("Chennai", "LOCATION", "A city where Orbit Logistics runs warehouses.", 10, "Orbit Logistics runs warehouses in Mumbai and Chennai."),
    ent("Acme Robotics", "ORGANIZATION", "A company that signed a supply contract with Orbit Logistics in 2022.", 9, "In 2022 Orbit Logistics signed a supply contract with Acme Robotics."),
    ent("supply contract", "OBJECT", "The contract signed between Orbit Logistics and Acme Robotics in 2022.", 8, "signed a supply contract with Acme Robotics"),
    ent("2022", "TEMPORAL", "The year the supply contract was signed.", 9, "In 2022 Orbit Logistics signed a supply contract"),
], [
    rel("Orbit Logistics", "Mumbai", "OPERATES", "Orbit Logistics runs warehouses in Mumbai.", 8, "Orbit Logistics runs warehouses in Mumbai and Chennai."),
    rel("Orbit Logistics", "Chennai", "OPERATES", "Orbit Logistics runs warehouses in Chennai.", 8, "Orbit Logistics runs warehouses in Mumbai and Chennai."),
    rel("Orbit Logistics", "Acme Robotics", "PARTNERS_WITH", "Orbit Logistics signed a supply contract with Acme Robotics in 2022.", 8, "In 2022 Orbit Logistics signed a supply contract with Acme Robotics."),
])
# 02_meera.txt
A["af258f25ff"] = reply([
    ent("Meera Shah", "PERSON", "A person who studied engineering at IIT Bombay and worked at Orbit Logistics as a hardware lead before Acme Robotics.", 10, "Meera Shah studied engineering at IIT Bombay."),
    ent("IIT Bombay", "ORGANIZATION", "The institution where Meera Shah studied engineering.", 10, "Meera Shah studied engineering at IIT Bombay."),
    ent("Acme Robotics", "ORGANIZATION", "A company Meera Shah was at after Orbit Logistics.", 8, "Before Acme Robotics she worked at Orbit Logistics as a hardware lead."),
    ent("Orbit Logistics", "ORGANIZATION", "A company where Meera Shah worked as a hardware lead before Acme Robotics.", 9, "she worked at Orbit Logistics as a hardware lead."),
], [
    rel("Meera Shah", "IIT Bombay", "STUDIED_AT", "Meera Shah studied engineering at IIT Bombay.", 8, "Meera Shah studied engineering at IIT Bombay."),
    rel("Meera Shah", "Orbit Logistics", "WORKED_AT", "Meera Shah worked at Orbit Logistics as a hardware lead before Acme Robotics.", 7, "she worked at Orbit Logistics as a hardware lead."),
])
# 05_investor.txt
A["e5a610dbad"] = reply([
    ent("Banyan Capital", "ORGANIZATION", "An investor in Acme Robotics since 2019.", 10, "Banyan Capital invested in Acme Robotics in 2019."),
    ent("Acme Robotics", "ORGANIZATION", "A company that Banyan Capital invested in in 2019.", 10, "Banyan Capital invested in Acme Robotics in 2019."),
    ent("2019", "TEMPORAL", "The year Banyan Capital invested in Acme Robotics.", 9, "Banyan Capital invested in Acme Robotics in 2019."),
    ent("Ravi Menon", "PERSON", "A partner at Banyan Capital who sits on the Acme board.", 10, "Ravi Menon, a partner at Banyan Capital, sits on the Acme board."),
    ent("Acme board", "ORGANIZATION", "The board of Acme Robotics, on which Ravi Menon sits.", 7, "sits on the Acme board."),
], [
    rel("Banyan Capital", "Acme Robotics", "INVESTED_IN", "Banyan Capital invested in Acme Robotics in 2019.", 9, "Banyan Capital invested in Acme Robotics in 2019."),
    rel("Ravi Menon", "Banyan Capital", "PART_OF", "Ravi Menon is a partner at Banyan Capital.", 8, "Ravi Menon, a partner at Banyan Capital"),
    rel("Ravi Menon", "Acme board", "PART_OF", "Ravi Menon sits on the Acme board.", 8, "sits on the Acme board."),
    rel("Acme board", "Acme Robotics", "PART_OF", "The Acme board is the board of Acme Robotics.", 7, "sits on the Acme board."),
])
# 04_product.txt
A["21733b78c0"] = reply([
    ent("Acme Picker X2", "OBJECT", "A warehouse robot that lifts up to 40 kg, used by Orbit Logistics in its Chennai warehouse.", 10, "The Acme Picker X2 is a warehouse robot that lifts up to 40 kg."),
    ent("Orbit Logistics", "ORGANIZATION", "A company that uses the Picker X2 in its Chennai warehouse.", 10, "Orbit Logistics uses the Picker X2 in its Chennai warehouse."),
    ent("Chennai", "LOCATION", "The city of the Orbit Logistics warehouse where the Picker X2 is used.", 9, "in its Chennai warehouse."),
], [
    rel("Orbit Logistics", "Acme Picker X2", "USES", "Orbit Logistics uses the Picker X2 in its Chennai warehouse.", 9, "Orbit Logistics uses the Picker X2 in its Chennai warehouse."),
    rel("Acme Picker X2", "Chennai", "LOCATED_IN", "The Picker X2 is used in the Orbit Logistics warehouse in Chennai.", 6, "uses the Picker X2 in its Chennai warehouse."),
])
json.dump(A, open("answers_stage5.json", "w"), indent=1, ensure_ascii=False); open("answers_stage5.json", "a").write("\n")
print(len(A), "answers written")
