import "@testing-library/jest-dom/vitest";
import * as matchers from "vitest-axe/matchers";
import React from "react";
import { expect, vi } from "vitest";

expect.extend(matchers);

vi.mock("next/image", () => ({
  default: ({
    src,
    alt,
    className,
  }: {
    src?: string | { src: string };
    alt?: string;
    className?: string;
    [key: string]: unknown;
  }) => {
    return React.createElement("img", {
      src:
        typeof src === "string"
          ? src
          : typeof src?.src === "string"
            ? src.src
            : "",
      alt: typeof alt === "string" ? alt : "",
      className: typeof className === "string" ? className : undefined,
    });
  },
}));
