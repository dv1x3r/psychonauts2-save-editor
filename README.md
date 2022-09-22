# Psychonauts 2 Save Editor

Psychonauts 2 uses Unreal Engine 4 save system, which is encoded in GVAS format. **Save slot** consists of **two .sav files**: Psychonauts2Save_[0,1,2].sav and Psychonauts2Save_[A,B,C].sav.  
  
The purpose of this script is to decode .sav file into human readable .json for further editing, and encoding it back to .sav.  

## Warning

- **Script is still in development, and not decoder is not fully operational.**  
- **Some data structures are still exported to .json in raw hex format.**  
- **Please do backups for your original .sav files.**  

## WIP Basics

Inside main.py file you can find 4 methods ready to use:
- `sav_to_gvas(sav_path: str)`: decoding .sav file into python Gvas object.
- `gvas_to_sav(gvas: Gvas, sav_path: str)`: writing python Gvas object back into .sav file.
- `gvas_to_json(gvas: Gvas, json_path: str)`: writing python Gvas object into human readable .json file for further editing.
- `json_to_gvas(json_path: str)`: reading .json file into python Gvas object.

## References

- [github.com/SparkyTD/UnrealEngine.Gvas](https://github.com/SparkyTD/UnrealEngine.Gvas)
- [github.com/13xforever/gvas-converter](https://github.com/13xforever/gvas-converter)
- [gist.github.com/Rob7045713/UeSaveSerializer.py](https://gist.github.com/Rob7045713/2f838ad66237f87c86d5396af573b71c)
