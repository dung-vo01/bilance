import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { Icon } from "@iconify/react";
import styles from "./SearchSelect.module.scss";

interface SelectOption {
  value: string;
  label: string;
}

interface Props {
  options: SelectOption[];
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  searchPlaceholder?: string;
  wrapperClassName?: string;
  triggerClassName?: string;
  maxHeight?: number;
}

export const SearchSelect = ({
  options,
  value,
  onChange,
  placeholder,
  searchPlaceholder = "Search...",
  wrapperClassName,
  triggerClassName,
  maxHeight = 180,
}: Props) => {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const [dropdownPos, setDropdownPos] = useState({ top: 0, left: 0, width: 0 });
  const ref = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const isMobile = window.innerWidth < 768;

  const selected = options.find((o) => o.value === value);
  const filtered = options.filter((o) =>
    o.label.toLowerCase().includes(search.toLowerCase()),
  );

  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      // On mobile, the full-screen backdrop's own onClick closes the dropdown
      // instead. Closing here on mousedown would unmount the backdrop before
      // iOS Safari's delayed synthetic click fires, letting that click fall
      // through onto whatever element ends up underneath.
      if (isMobile) return;
      if (
        ref.current &&
        !ref.current.contains(e.target as Node) &&
        dropdownRef.current &&
        !dropdownRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
        setSearch("");
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 50);
    } else {
      setSearch("");
    }
  }, [open]);

  useEffect(() => {
    if (!open) return;
    const handleScroll = () => updatePosition();
    window.addEventListener("scroll", handleScroll, true);
    return () => window.removeEventListener("scroll", handleScroll, true);
  }, [open]);

  const updatePosition = () => {
    if (ref.current) {
      const rect = ref.current.getBoundingClientRect();
      setDropdownPos({
        top: rect.bottom + 4,
        left: rect.left,
        width: rect.width,
      });
    }
  };

  const handleOpen = () => {
    updatePosition();
    setOpen((prev) => !prev);
  };

  const handleSelect = (optionValue: string) => {
    onChange(optionValue);
    setOpen(false);
    setSearch("");
  };

  const dropdown = open ? (
    <>
      {isMobile && (
        <div
          style={{
            position: "fixed",
            inset: 0,
            background: "rgba(0,0,0,0.4)",
            zIndex: 999,
          }}
          onClick={() => setOpen(false)}
        />
      )}
      <div
        className={styles.dropdown}
        ref={dropdownRef}
        data-portal-dropdown="true"
        style={
          isMobile
            ? undefined
            : {
                position: "fixed",
                top: dropdownPos.top,
                left: dropdownPos.left,
                width: dropdownPos.width,
                zIndex: 1000,
              }
        }
      >
        <div className={styles.searchWrap}>
          <Icon
            icon="ph:magnifying-glass"
            width={14}
            height={14}
            className={styles.searchIcon}
          />
          <input
            ref={inputRef}
            className={styles.searchInput}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={searchPlaceholder}
          />
          {search && (
            <button
              type="button"
              className={styles.clearBtn}
              onClick={() => setSearch("")}
            >
              <Icon icon="ph:x" width={12} height={12} />
            </button>
          )}
        </div>

        <div
          className={styles.optionList}
          style={isMobile ? undefined : { maxHeight, overflowY: "auto" }}
        >
          {filtered.length === 0 ? (
            <div className={styles.empty}>No results</div>
          ) : (
            filtered.map((option) => (
              <button
                key={option.value}
                type="button"
                className={`${styles.option} ${option.value === value ? styles.optionSelected : ""}`}
                onClick={() => handleSelect(option.value)}
              >
                {option.label}
                {option.value === value && (
                  <Icon
                    icon="ph:check"
                    width={14}
                    height={14}
                    className={styles.checkIcon}
                  />
                )}
              </button>
            ))
          )}
        </div>
      </div>
    </>
  ) : null;

  return (
    <div ref={ref} className={`${styles.wrapper} ${wrapperClassName ?? ""}`}>
      <button
        type="button"
        className={`${styles.trigger} ${triggerClassName ?? ""} ${open ? styles.triggerOpen : ""}`}
        onClick={handleOpen}
      >
        <span
          className={selected ? styles.triggerValue : styles.triggerPlaceholder}
        >
          {selected?.label ?? placeholder ?? "Select..."}
        </span>
        <Icon
          icon={open ? "ph:caret-up" : "ph:caret-down"}
          width={14}
          height={14}
          className={styles.arrow}
        />
      </button>

      {createPortal(dropdown, document.body)}
    </div>
  );
};
