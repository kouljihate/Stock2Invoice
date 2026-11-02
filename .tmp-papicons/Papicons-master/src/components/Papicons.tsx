import React from 'react';
import * as Icons from '../icons-web';
import type { PapiconsProps } from '../types/PapiconsProps';
import { IconNames } from '../icons-web';

type WebSvgProps = React.SVGProps<SVGSVGElement>;

function Papicons({
  name,
  ...props
}: {
  name: IconNames | string;
} & WebSvgProps & PapiconsProps): React.JSX.Element {
  if (name) {
    const IconComponent = Object.entries(Icons).find(
      ([key]) => key.toLowerCase() === name.toLowerCase()
    )?.[1] as React.ComponentType<WebSvgProps>;

    if (IconComponent) {
      return <IconComponent {...props} />;
    }
  }

  console.warn(`Papicons icon "${name}" does not exist.`);
  return <Icons.Placeholder {...props} />;
}

export default Papicons;
