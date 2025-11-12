"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.CosmeticsSchema = exports.PatternInfoSchema = exports.PatternSchema = exports.PatternNameSchema = exports.ProductSchema = void 0;
const jose_1 = require("jose");
const v4_1 = require("zod/v4");
const PatternDecoder_1 = require("./PatternDecoder");
exports.ProductSchema = v4_1.z.object({
    productId: v4_1.z.string(),
    priceId: v4_1.z.string(),
    price: v4_1.z.string(),
});
exports.PatternNameSchema = v4_1.z
    .string()
    .regex(/^[a-z0-9_]+$/)
    .max(32);
exports.PatternSchema = v4_1.z
    .string()
    .max(1403)
    .base64url()
    .refine((val) => {
    try {
        new PatternDecoder_1.PatternDecoder(val, jose_1.base64url.decode);
        return true;
    }
    catch (e) {
        if (e instanceof Error) {
            console.error(JSON.stringify(e.message, null, 2));
        }
        else {
            console.error(String(e));
        }
        return false;
    }
}, {
    message: "Invalid pattern",
});
exports.PatternInfoSchema = v4_1.z.object({
    name: exports.PatternNameSchema,
    pattern: exports.PatternSchema,
    product: exports.ProductSchema.nullable(),
});
// Schema for resources/cosmetics/cosmetics.json
exports.CosmeticsSchema = v4_1.z.object({
    patterns: v4_1.z.record(v4_1.z.string(), exports.PatternInfoSchema),
    flag: v4_1.z
        .object({
        layers: v4_1.z.record(v4_1.z.string(), v4_1.z.object({
            name: v4_1.z.string(),
            flares: v4_1.z.array(v4_1.z.string()).optional(),
        })),
        color: v4_1.z.record(v4_1.z.string(), v4_1.z.object({
            color: v4_1.z.string(),
            name: v4_1.z.string(),
            flares: v4_1.z.array(v4_1.z.string()).optional(),
        })),
    })
        .optional(),
});
