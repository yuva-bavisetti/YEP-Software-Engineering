import React from "react";
const House = React.lazy(() => import("../House"));
export default function HouseScene() {
  return (
    <React.Suspense
      fallback={
        <div className="house">
          <div className="house-fallback">⌂</div>
        </div>
      }
    >
      <House />
    </React.Suspense>
  );
}
