import fs from "fs";
import path from "path";
import type { Plugin } from "vite";

/**
 * Vite plugin that updates og:image and twitter:image meta tags
 * to point to the app's opengraph image.
 */
export function metaImagesPlugin(): Plugin {
  return {
    name: "vite-plugin-meta-images",
    transformIndexHtml(html) {
      // Check if opengraph image exists in public directory
      const publicDir = path.resolve(process.cwd(), "public");
      const opengraphPngPath = path.join(publicDir, "opengraph.png");
      const opengraphJpgPath = path.join(publicDir, "opengraph.jpg");
      const opengraphJpegPath = path.join(publicDir, "opengraph.jpeg");

      let imageExt: string | null = null;
      if (fs.existsSync(opengraphPngPath)) {
        imageExt = "png";
      } else if (fs.existsSync(opengraphJpgPath)) {
        imageExt = "jpg";
      } else if (fs.existsSync(opengraphJpegPath)) {
        imageExt = "jpeg";
      }

      if (!imageExt) {
        return html;
      }

      const imageUrl = `/opengraph.${imageExt}`;

      html = html.replace(
        /<meta\s+property="og:image"\s+content="[^"]*"\s*\/>/g,
        `<meta property="og:image" content="${imageUrl}" />`
      );

      html = html.replace(
        /<meta\s+name="twitter:image"\s+content="[^"]*"\s*\/>/g,
        `<meta name="twitter:image" content="${imageUrl}" />`
      );

      return html;
    },
  };
}
