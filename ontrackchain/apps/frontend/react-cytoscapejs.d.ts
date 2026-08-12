declare module "react-cytoscapejs" {
  import type { ElementDefinition, LayoutOptions, Stylesheet } from "cytoscape";
  import type { ComponentType, CSSProperties } from "react";

  export interface CytoscapeComponentProps {
    elements: ElementDefinition[] | any[];
    style?: CSSProperties;
    layout?: LayoutOptions | any;
    stylesheet?: Stylesheet | Stylesheet[] | any;
    cy?: (cy: any) => void;
    className?: string;
    [key: string]: any;
  }

  const CytoscapeComponent: ComponentType<CytoscapeComponentProps>;
  export default CytoscapeComponent;
}
