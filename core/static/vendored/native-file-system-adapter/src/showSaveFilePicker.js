const native=globalThis.showSaveFilePicker;async function showSaveFilePicker(e={}){if(native&&!e._preferPolyfill)return native(e);e._name&&(console.warn("deprecated _name, spec now have `suggestedName`"),e.suggestedName=e._name);const{FileSystemFileHandle:a}=await import("./FileSystemFileHandle.js"),{FileHandle:i}=await import("./adapters/downloader.js");return new a(new i(e.suggestedName))}export default showSaveFilePicker;export{showSaveFilePicker};