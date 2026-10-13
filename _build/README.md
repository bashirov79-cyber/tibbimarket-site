# tibbimarket.az — generator
- data.json: saytın bütün məlumatı.
- Yeniləmə (repo kökündən): python3 _build/build.py . _build/data.json tibbimarket.az agizgenislendirici changes.json
- Dəyişiklik olmadan işə salsan, sayt hərfi-hərfinə eyni qalır.
- Dərc: push → cPanel › Git Version Control › Update from Remote → Deploy HEAD Commit.
- Kataloqdan yeniləmə: python3 _build/sync_from_catalog.py <medishop-kataloq qovluğu> report | make [placement.json] — sonra build.
