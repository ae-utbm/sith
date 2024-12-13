/**
 * A key of an object, or of one of its descendants.
 *
 * Example :
 * ```typescript
 * interface Foo {
 *   foo_inner: number;
 * }
 *
 * interface Bar {
 *   foo: Foo;
 * }
 *
 * const foo = (key: NestedKeyOf<Bar>) {
 *     console.log(key);
 * }
 *
 * foo("foo.foo_inner");  // OK
 * foo("foo.bar"); // FAIL
 * ```
 */
export type NestedKeyOf<T extends object> = {
  [Key in keyof T & (string | number)]: NestedKeyOfHandleValue<T[Key], `${Key}`>;
}[keyof T & (string | number)];

type NestedKeyOfInner<T extends object> = {
  [Key in keyof T & (string | number)]: NestedKeyOfHandleValue<
    T[Key],
    `['${Key}']` | `.${Key}`
  >;
}[keyof T & (string | number)];

type NestedKeyOfHandleValue<T, Text extends string> = T extends unknown[]
  ? Text
  : T extends object
    ? Text | `${Text}${NestedKeyOfInner<T>}`
    : Text;
