import { bundle } from "./tools/bundle.mjs";
import { bundle_css } from "./tools/css.mjs";
import { node_modules_external } from "./tools/externals.mjs";

import fs from "fs";
import cpy from "cpy";

const BUNDLES = [
  {
    entryPoints: ["src/ts/index.ts"],
<<<<<<< before updating
    plugins: [],
    format: "esm",
    loader: {
      ".css": "text",
      ".html": "text",
    },
=======
    plugins: [node_modules_external()],
    outfile: "dist/esm/index.js",
  },
  {
    entryPoints: ["src/ts/index.ts"],
>>>>>>> after updating
    outfile: "dist/cdn/index.js",
  },
];

<<<<<<< before updating
async function compile_css() {
  const process_path = (path) => {
    const outpath = path.replace("src/css", "dist/css");
    fs.mkdirSync(outpath, { recursive: true });

    fs.readdirSync(path, { withFileTypes: true }).forEach((entry) => {
      const input = `${path}/${entry.name}`;
      const output = `${outpath}/${entry.name}`;

      if (entry.isDirectory()) {
        process_path(input);
      } else if (entry.isFile() && entry.name.endsWith(".css")) {
        const source = fs.readFileSync(input);
        const { code } = transform({
          filename: entry.name,
          code: source,
          minify: !DEBUG,
          sourceMap: false,
        });
        fs.writeFileSync(output, code);
      }
    });
  };

  process_path("src/css");

  const shoelaceLight = new URL(
    "./node_modules/@shoelace-style/shoelace/dist/themes/light.css",
    import.meta.url,
  ).pathname;
  const { code } = transform({
    filename: "light.css",
    code: fs.readFileSync(shoelaceLight),
    minify: !DEBUG,
    sourceMap: false,
  });
  fs.mkdirSync("dist/css", { recursive: true });
  fs.writeFileSync("dist/css/light.css", code);
}

async function copy_to_python() {
  fs.mkdirSync("../airflow_balancer/ui/static", { recursive: true });
  cpy("dist/**/*", "../airflow_balancer/ui/static");
}

async function build_all() {
  await compile_css();
  await Promise.all(BUILD.map(build)).catch(() => process.exit(1));
  await copy_to_python();
=======
async function build() {
  // Bundle css
  await bundle_css();

  // Copy HTML
  cpy("src/html/*", "dist/");

  // Copy images
  fs.mkdirSync("dist/img", { recursive: true });
  cpy("src/img/*", "dist/img");

  await Promise.all(BUNDLES.map(bundle)).catch(() => process.exit(1));

  // Copy servable assets to python extension (exclude esm/)
  fs.mkdirSync("../airflow_balancer/extension", { recursive: true });
  cpy("dist/**/*", "../airflow_balancer/extension", {
    filter: (file) => !file.relativePath.startsWith("esm"),
  });
>>>>>>> after updating
}

build();
