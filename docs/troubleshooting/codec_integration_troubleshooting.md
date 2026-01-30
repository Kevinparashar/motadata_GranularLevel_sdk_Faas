# MOTADATA - CODEC INTEGRATION TROUBLESHOOTING

**Troubleshooting guide for diagnosing and resolving common issues with the CODEC Integration component.**

## Common Issues and Solutions

### Encoding Issues

#### Problem: Encoding Fails

**Symptoms:**
- `encode()` raises exception
- Data cannot be serialized

**Possible Causes:**
1. Unsupported data types
2. Circular references
3. Schema validation failure
4. Data too large

**Resolution Steps:**

1. **Check Data Types:**
   ```python
   # Ensure all data types are serializable
   # Convert datetime to ISO format strings
   # Convert complex objects to dictionaries
   ```

2. **Verify Schema:**
   ```python
   # Check data matches schema
   # Validate before encoding
   is_valid = codec.validate_schema(data, schema_name="agent_message")
   if not is_valid:
       raise ValueError("Data does not match schema")
   ```

3. **Handle Large Data:**
   ```python
   # For large payloads, consider chunking
   # Or use compression
   ```

---

#### Problem: Encoding Slow

**Symptoms:**
- Encoding takes > 1ms
- Performance degradation

**Possible Causes:**
1. Large payloads
2. Inefficient serialization
3. Schema validation overhead

**Resolution Steps:**

1. **Optimize Payload Size:**
   ```python
   # Remove unnecessary data
   # Compress large fields
   # Use efficient data structures
   ```

2. **Cache Envelopes:**
   ```python
   # Cache envelope templates
   # Only update data fields
   ```

3. **Disable Validation in Production:**
   ```python
   # Skip validation for trusted sources
   # Only validate in development
   ```

---

### Decoding Issues

#### Problem: Decoding Fails

**Symptoms:**
- `decode()` raises exception
- Invalid payload format

**Possible Causes:**
1. Corrupted payload
2. Wrong schema version
3. Invalid encoding format

**Resolution Steps:**

1. **Verify Payload Integrity:**
   ```python
   # Check payload is not corrupted
   # Verify payload format
   ```

2. **Handle Schema Version Mismatch:**
   ```python
   envelope = codec.decode(payload)
   if envelope["schema_version"] != current_version:
       # Migrate to current version
       envelope = codec.migrate_envelope(envelope, target_version=current_version)
   ```

3. **Validate After Decoding:**
   ```python
   envelope = codec.decode(payload)
   is_valid = codec.validate_schema(envelope, schema_name="agent_message")
   if not is_valid:
       raise ValueError("Invalid schema")
   ```

---

#### Problem: Decoding Returns Wrong Data

**Symptoms:**
- Decoded data doesn't match original
- Fields missing or incorrect

**Possible Causes:**
1. Schema version mismatch
2. Migration errors
3. Data corruption

**Resolution Steps:**

1. **Verify Schema Version:**
   ```python
   # Check schema version matches
   # Handle version migration correctly
   ```

2. **Test Round-Trip:**
   ```python
   # Test encode-decode round-trip
   original = {"key": "value"}
   encoded = codec.encode(original)
   decoded = codec.decode(encoded)
   assert decoded == original
   ```

3. **Add Validation:**
   ```python
   # Validate decoded data
   # Check required fields present
   ```

---

### Schema Validation Issues

#### Problem: Schema Validation Fails

**Symptoms:**
- Valid data fails validation
- False positive validation errors

**Possible Causes:**
1. Schema definition incorrect
2. Data format mismatch
3. Validation too strict

**Resolution Steps:**

1. **Verify Schema Definition:**
   ```python
   # Check schema matches actual data structure
   # Update schema if needed
   ```

2. **Check Data Format:**
   ```python
   # Ensure data matches expected format
   # Convert types if necessary
   ```

3. **Adjust Validation Level:**
   ```python
   # Use appropriate validation strictness
   # Relax validation for optional fields
   ```

---

#### Problem: Schema Version Mismatch

**Symptoms:**
- Old schema version messages fail
- Migration errors

**Possible Causes:**
1. Missing migration logic
2. Incompatible schema changes
3. Migration bugs

**Resolution Steps:**

1. **Implement Migration:**
   ```python
   # Handle version migration
   if envelope["schema_version"] != current_version:
       envelope = codec.migrate_envelope(
           envelope,
           target_version=current_version
       )
   ```

2. **Test Migrations:**
   ```python
   # Test all version migrations
   # Ensure backward compatibility
   ```

3. **Version Compatibility:**
   ```python
   # Support multiple schema versions
   # Gracefully handle unsupported versions
   ```

---

### Performance Issues

#### Problem: Serialization Slow

**Symptoms:**
- Encoding/decoding > 1ms
- High CPU usage

**Possible Causes:**
1. Large payloads
2. Inefficient encoding format
3. Excessive validation

**Resolution Steps:**

1. **Use Efficient Format:**
   ```python
   # Prefer MessagePack over JSON for performance
   # Use binary formats when possible
   ```

2. **Optimize Validation:**
   ```python
   # Cache validation results
   # Skip validation for trusted sources
   ```

3. **Profile Serialization:**
   ```python
   import cProfile
   cProfile.run('codec.encode(data)')
   # Identify bottlenecks
   ```

---

## Best Practices

1. **Schema Management:**
   - Version schemas properly
   - Maintain backward compatibility
   - Document schema changes

2. **Error Handling:**
   - Always validate after decode
   - Handle version mismatches gracefully
   - Log encoding/decoding errors

3. **Performance:**
   - Use efficient encoding formats
   - Minimize payload size
   - Cache envelope templates

4. **Testing:**
   - Test round-trip encoding/decoding
   - Test version migrations
   - Test with various data sizes

---

## See Also

- [CODEC Integration Guide](../../integration_guides/codec_integration_guide.md)
- [CORE_COMPONENTS_INTEGRATION_STORY.md](../../../CORE_COMPONENTS_INTEGRATION_STORY.md)
- Core SDK CODEC documentation

