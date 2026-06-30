import crypto from "crypto";

const DEFAULT_TOTP_SECRET = process.env.MFA_TOTP_SECRET || "JBSWY3DPEHPK3PXP";

function decodeBase32(secret: string): Uint8Array {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
  const normalized = secret.replace(/[\s=]+/g, "").toUpperCase();
  let bits = "";
  for (const char of normalized) {
    const index = alphabet.indexOf(char);
    if (index === -1) {
      throw new Error("invalid_totp_secret");
    }
    bits += index.toString(2).padStart(5, "0");
  }

  const bytes: number[] = [];
  for (let offset = 0; offset + 8 <= bits.length; offset += 8) {
    bytes.push(parseInt(bits.slice(offset, offset + 8), 2));
  }
  return Uint8Array.from(bytes);
}

export function generateTotpCode(secret = DEFAULT_TOTP_SECRET, timestamp = Date.now()): string {
  const key = decodeBase32(secret);
  const counter = Math.floor(timestamp / 1000 / 30);
  const buffer = new ArrayBuffer(8);
  new DataView(buffer).setBigUint64(0, BigInt(counter));
  const digest = crypto.createHmac("sha1", key).update(new Uint8Array(buffer)).digest();
  const offset = digest[digest.length - 1] & 0x0f;
  const binary = (digest.readUInt32BE(offset) & 0x7fffffff) % 1_000_000;
  return binary.toString().padStart(6, "0");
}
