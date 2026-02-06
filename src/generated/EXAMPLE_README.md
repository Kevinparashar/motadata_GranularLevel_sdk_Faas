# Generated Code Examples

This directory will contain **auto-generated code** when Protocol Buffers or other code generators are used.

## Example: Protocol Buffer Files

When you have a `.proto` file and generate Python code, the output files will look like:

```
generated/
└── protobuf/
    ├── service_pb2.py          # Generated from service.proto
    └── service_pb2_grpc.py     # Generated gRPC code
```

### How to Generate (Example)

```bash
# Install protoc compiler
# Then generate Python code:
protoc --python_out=src/generated/protobuf \
       --grpc_python_out=src/generated/protobuf \
       your_service.proto
```

## Example: Generated Code Files

Files matching `*_gen.py` pattern would be placed here:

```
generated/
└── api_gen.py          # Auto-generated API client code
```

## Important Notes

1. **Never manually edit** files in this directory
2. **Regenerate from source** when `.proto` files change
3. **Version control** the source files (`.proto`), not generated files
4. **Coverage exclusion** - Generated code is excluded from coverage

---

**Status:** This directory is ready for generated code when needed.

