import styles from "./Footer.module.scss";

interface Props {
  className?: string;
}

export const Footer = ({ className }: Props) => (
  <footer className={`${styles.footer} ${className ?? ""}`}>
    &copy; {new Date().getFullYear()} Dung Vo. All rights reserved.
  </footer>
);
