#!/usr/bin/env python3
"""Update repodata.json with a new .conda package. Removes old versions of the same package."""
import json, zipfile, subprocess, io, tarfile, hashlib, os, sys

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <path-to-package.conda>")
        sys.exit(1)

    pkg_path = sys.argv[1]
    pkg_fname = os.path.basename(pkg_path)

    # Read package metadata
    with open(pkg_path, "rb") as f:
        pkg_bytes = f.read()
    sha256 = hashlib.sha256(pkg_bytes).hexdigest()
    fsize = len(pkg_bytes)

    z = zipfile.ZipFile(pkg_path)
    info_name = [n for n in z.namelist() if n.startswith("info-")][0]
    info_zst = z.read(info_name)
    p = subprocess.run(["zstd", "-d", "-c"], input=info_zst, capture_output=True, check=True)
    t = tarfile.open(fileobj=io.BytesIO(p.stdout))
    index_data = json.loads(t.extractfile("info/index.json").read())

    index_data["size"] = fsize
    index_data["sha256"] = sha256
    pkg_name = index_data["name"]

    # Load existing repodata
    repodata_path = "linux-64/repodata.json"
    if os.path.exists(repodata_path):
        with open(repodata_path) as f:
            repodata = json.load(f)
    else:
        repodata = {"info": {"subdir": "linux-64"}, "packages": {}, "packages.conda": {}, "removed": [], "repodata_version": 2}

    # Remove old versions of the same package
    to_remove = [k for k, v in repodata["packages.conda"].items() if v.get("name") == pkg_name]
    for k in to_remove:
        print(f"Removing old: {k}")
        del repodata["packages.conda"][k]

    # Add new
    repodata["packages.conda"][pkg_fname] = index_data
    with open(repodata_path, "w") as f:
        json.dump(repodata, f, indent=2)

    print(f"Added: {pkg_fname} ({pkg_name} {index_data['version']})")

if __name__ == "__main__":
    main()
