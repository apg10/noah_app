import React from "react";

interface LayoutContainerProps {
  children: React.ReactNode;
  className?: string;
}

export const LayoutContainer: React.FC<LayoutContainerProps> = ({
  children,
  className = "",
}) => {
  return <div className={`layout-container ${className}`}>{children}</div>;
};
