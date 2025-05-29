import { render } from "@testing-library/react";
import SkeletonLoader from "../SkeletonLoader";

describe("SkeletonLoader", () => {
  it("renders rectangular skeleton by default", () => {
    render(<SkeletonLoader />);

    // Check for the skeleton element with animation classes
    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass("animate-pulse", "bg-gray-200", "rounded");
  });

  it("renders text skeleton with multiple lines", () => {
    render(<SkeletonLoader variant="text" lines={3} />);

    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons).toHaveLength(3);

    // Last line should be shorter (75% width)
    const lastSkeleton = skeletons[skeletons.length - 1];
    expect(lastSkeleton).toHaveClass("w-3/4");
  });

  it("renders circular skeleton", () => {
    render(<SkeletonLoader variant="circular" />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toBeInTheDocument();
    expect(skeleton).toHaveClass("rounded-full");
  });

  it("renders card skeleton with title and content", () => {
    render(<SkeletonLoader variant="card" />);

    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons.length).toBeGreaterThan(1);

    // Should have card container
    const cardContainer = document.querySelector(".p-4.border");
    expect(cardContainer).toBeInTheDocument();
    expect(cardContainer).toHaveClass("rounded-lg");
  });

  it("applies custom width and height", () => {
    render(<SkeletonLoader width="200px" height="100px" />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toHaveStyle({
      width: "200px",
      height: "100px"
    });
  });

  it("applies custom width and height as numbers", () => {
    render(<SkeletonLoader width={300} height={150} />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toHaveStyle({
      width: "300px",
      height: "150px"
    });
  });

  it("applies custom className", () => {
    render(<SkeletonLoader className="custom-class" />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toHaveClass("custom-class");
  });

  it("renders correct number of text lines", () => {
    render(<SkeletonLoader variant="text" lines={5} />);

    const skeletons = document.querySelectorAll(".animate-pulse");
    expect(skeletons).toHaveLength(5);
  });

  it("has proper dark mode classes", () => {
    render(<SkeletonLoader />);

    const skeleton = document.querySelector(".animate-pulse");
    expect(skeleton).toHaveClass("bg-gray-200", "dark:bg-gray-700");
  });

  it("text variant applies space between lines", () => {
    render(<SkeletonLoader variant="text" lines={3} />);

    const container = document.querySelector(".space-y-2");
    expect(container).toBeInTheDocument();
  });

  it("card variant has proper structure", () => {
    render(<SkeletonLoader variant="card" />);

    // Check for card container
    const cardContainer = document.querySelector(".p-4.border");
    expect(cardContainer).toBeInTheDocument();

    // Check for title skeleton
    const titleSkeleton = document.querySelector(".h-6.w-3\\/4.mb-3");
    expect(titleSkeleton).toBeInTheDocument();

    // Check for content lines container
    const contentContainer = document.querySelector(".space-y-2");
    expect(contentContainer).toBeInTheDocument();

    // Should have multiple content lines
    const contentLines = document.querySelectorAll(".h-4");
    expect(contentLines.length).toBeGreaterThanOrEqual(3);
  });
});
