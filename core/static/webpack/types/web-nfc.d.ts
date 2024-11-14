// Type definitions for Web NFC
// Project: https://github.com/w3c/web-nfc
// Definitions by: Takefumi Yoshii <https://github.com/takefumi-yoshii>
// TypeScript Version: 3.9

// This type definitions referenced to WebIDL.
// https://w3c.github.io/web-nfc/#actual-idl-index

// This has been modified to not trigger biome linting

// biome-ignore lint/correctness/noUnusedVariables: this is the official definition
interface Window {
  // biome-ignore lint/style/useNamingConvention: this is the official API name
  NDEFMessage: NDEFMessage;
}

// biome-ignore lint/style/useNamingConvention: this is the official API name
declare class NDEFMessage {
  constructor(messageInit: NDEFMessageInit);
  records: readonly NDEFRecord[];
}

// biome-ignore lint/style/useNamingConvention: this is the official API name
declare interface NDEFMessageInit {
  records: NDEFRecordInit[];
}

// biome-ignore lint/style/useNamingConvention: this is the official API name
declare type NDEFRecordDataSource = string | BufferSource | NDEFMessageInit;

// biome-ignore lint/correctness/noUnusedVariables: this is the official definition
interface Window {
  // biome-ignore lint/style/useNamingConvention: this is the official API name
  NDEFRecord: NDEFRecord;
}
// biome-ignore lint/style/useNamingConvention: this is the official API name
declare class NDEFRecord {
  constructor(recordInit: NDEFRecordInit);
  readonly recordType: string;
  readonly mediaType?: string;
  readonly id?: string;
  readonly data?: DataView;
  readonly encoding?: string;
  readonly lang?: string;
  toRecords?: () => NDEFRecord[];
}
// biome-ignore lint/style/useNamingConvention: this is the official API name
declare interface NDEFRecordInit {
  recordType: string;
  mediaType?: string;
  id?: string;
  encoding?: string;
  lang?: string;
  data?: NDEFRecordDataSource;
}

// biome-ignore lint/style/useNamingConvention: this is the official API name
declare type NDEFMessageSource = string | BufferSource | NDEFMessageInit;

// biome-ignore lint/correctness/noUnusedVariables: this is the official definition
interface Window {
  // biome-ignore lint/style/useNamingConvention: this is the official API name
  NDEFReader: NDEFReader;
}
// biome-ignore lint/style/useNamingConvention: this is the official API name
declare class NDEFReader extends EventTarget {
  constructor();
  // biome-ignore lint/suspicious/noExplicitAny: who am I to doubt the w3c definitions ?
  onreading: (this: this, event: NDEFReadingEvent) => any;
  // biome-ignore lint/suspicious/noExplicitAny: who am I to doubt the w3c definitions ?
  onreadingerror: (this: this, error: Event) => any;
  scan: (options?: NDEFScanOptions) => Promise<void>;
  write: (message: NDEFMessageSource, options?: NDEFWriteOptions) => Promise<void>;
  makeReadOnly: (options?: NDEFMakeReadOnlyOptions) => Promise<void>;
}

// biome-ignore lint/correctness/noUnusedVariables: this is the official definition
interface Window {
  // biome-ignore lint/style/useNamingConvention: this is the official API name
  NDEFReadingEvent: NDEFReadingEvent;
}
// biome-ignore lint/style/useNamingConvention: this is the official API name
declare class NDEFReadingEvent extends Event {
  constructor(type: string, readingEventInitDict: NDEFReadingEventInit);
  serialNumber: string;
  message: NDEFMessage;
}
// biome-ignore lint/style/useNamingConvention: this is the official API name
interface NDEFReadingEventInit extends EventInit {
  serialNumber?: string;
  message: NDEFMessageInit;
}

// biome-ignore lint/style/useNamingConvention: this is the official API name
interface NDEFWriteOptions {
  overwrite?: boolean;
  signal?: AbortSignal;
}
// biome-ignore lint/style/useNamingConvention: this is the official API name
interface NDEFMakeReadOnlyOptions {
  signal?: AbortSignal;
}
// biome-ignore lint/style/useNamingConvention: this is the official API name
interface NDEFScanOptions {
  signal: AbortSignal;
}
