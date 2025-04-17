# Cinemata mediacms-frontend

### **Requirements**

- nodejs lts version **16.13.x**

---

### Pre-installation

This pre-installation refers to specific sub-packages within the folder, namely `packages/media-player` and `packages/vjs-plugin`. The pre-installation will be done for both of them.

1. Both files should have tarballs (.tgz) in them. Unzip these tarballs by double-clicking them and you should have a newly created `/package` folder.
- **For vjs-plugin**: This folder has a subfolder called `/packages/vjs-plugin-font-icons` which also has a tarball that needs to be unzipped which will also produce a `/dist` folder.

2. For all folders (`/packages/media-player`, `/packages/vjs-plugin`, `packages/vjs-plugin/packages/vjs-plugin-font-icons`), using the Terminal, execute `npm install` to install their respective dependencies.

3. After these dependencies are installed, as indicated by the presence of `node_modules/` in each folder, proceed to execute `npm run build` to create the `/dist` folder for each subfolder.

> [!WARN]
> At this point, make sure that the `/dist` folders for `vjs-plugin` and `media-player` have `.css` and `.js` files. If they are missing any file, you may copy the `.css`/`.js` file/s found within their respective `/package/dist` subfolders. This will be important for the installation, development, and build steps listed below.

---

### **Installation**

    npm install

---

### **Development**

    npm run start

Open in browser: [localhost:8088](http://localhost:8088)

- Sitemap: [localhost:8088/sitemap.html](http://localhost:8088/sitemap.html)

---

### **Build**

    npm run build

Generates the folder "**_build/production_**".

---

### **Transfer files into backend/server (django root)**

Copy files and folders:

- from "**_build/production/_**" into "**_static/_**"
