# Feature Specification: Provider模型统一切换至llm CLI

**Feature Branch**: `006-provider-llm-cli`
**Created**: 2025-10-17
**Status**: Draft
**Input**: User description: "调整 provider 模型以全面切换至 llm CLI"

## Execution Flow (main)
```
1. Parse user description from Input
   → Feature description provided and parsed
2. Extract key concepts from description
   → Identified: LLM provider abstraction, CLI command unification, DeepSeek integration
3. For each unclear aspect:
   → ✅ RESOLVED: DeepSeek使用标准llm CLI接口（llm -m deepseek-coder/deepseek-chat）
   → ✅ RESOLVED: 完全移除Gemini，由llm CLI统一管理模型切换
   → ✅ RESOLVED: Provider失败采用fail-fast策略，超长prompt直接报错
   → ✅ RESOLVED: 批量场景不在MVP范围
4. Fill User Scenarios & Testing section
   → Completed based on available information
5. Generate Functional Requirements
   → All requirements are testable
6. Identify Key Entities
   → Completed
7. Run Review Checklist
   → ✅ PASS: All critical ambiguities resolved via clarification session
8. Return: SUCCESS (spec ready for planning)
```

---

## ⚡ Quick Guidelines
- ✅ Focus on WHAT users need and WHY
- ❌ Avoid HOW to implement (no tech stack, APIs, code structure)
- 👥 Written for business stakeholders, not developers

---

## Clarifications

### Session 2025-10-17

- Q: DeepSeek是否通过标准llm CLI调用？ → A: 是，使用标准llm CLI接口（`llm -m deepseek-coder/deepseek-chat "prompt"`），无需特殊参数
- Q: Gemini provider应如何处理？ → A: 完全移除Gemini支持，llm-deepseek分支彻底清理Gemini代码，后续模型切换由llm CLI统一管理
- Q: Provider不可用时应如何响应？ → A: 立即失败并报错，遵循fail-fast原则，不实现自动降级或重试
- Q: 超长prompt（超过context window）应如何处理？ → A: 直接报错并提示限制，避免自动截断导致的语义风险
- Q: 批量生成报告场景是否在本次功能范围内？ → A: 不在范围内，MVP保持单线程、单任务执行模式

---

## User Scenarios & Testing *(mandatory)*

### Primary User Story
作为Code Score系统的运维人员，我需要系统能够支持多个LLM provider（特别是DeepSeek），而不是只能使用Gemini，这样可以在成本、性能和可用性之间做出灵活选择。当前系统对Gemini有硬编码依赖，无法快速切换到其他provider。

### Acceptance Scenarios

1. **Given** 系统已配置DeepSeek provider，**When** 用户执行LLM报告生成命令时，**Then** 系统使用llm CLI调用DeepSeek生成报告，而不是调用Gemini

2. **Given** 用户提供了自定义provider配置（模型名、超时、环境变量等），**When** 系统执行报告生成时，**Then** 系统根据配置正确拼装llm CLI命令行并执行

3. **Given** 用户未提供provider配置，**When** 系统启动报告生成时，**Then** 系统使用默认的DeepSeek配置（或通过配置文件指定的默认provider）

4. **Given** provider配置缺少必需的环境变量（如API密钥），**When** 系统验证配置时，**Then** 系统明确报告缺失的环境变量名称，并拒绝执行

5. **Given** 用户在命令行指定了dry-run模式，**When** 系统准备执行LLM调用时，**Then** 系统输出将要执行的llm CLI命令，但不实际执行，供用户验证

### Edge Cases

- **Provider不可用时的响应**: 当DeepSeek不可用（网络故障、API限流、认证失败）时，系统立即失败并返回明确错误信息，遵循fail-fast原则，不实现自动降级或重试机制

- **llm CLI可用性检测**: 系统在执行前验证llm CLI是否已安装（通过`llm --version`），若未安装或版本过旧，提供安装指引和文档链接，拒绝继续执行

- **超长prompt处理**: 当评估数据生成的prompt超过provider的context window上限时，系统直接报错并提示具体限制（如"Prompt长度12000 tokens超过DeepSeek上限8192 tokens"），避免自动截断导致的语义风险

- **并发与批量场景**: 批量生成报告不在MVP范围内，系统保持单线程、单任务执行模式，不实现请求队列或速率限流功能

---

## Requirements *(mandatory)*

### Functional Requirements

#### Provider抽象与配置

- **FR-001**: 系统MUST移除对Gemini的硬编码检查（LLMProviderConfig.validate_provider_name中的allowed_providers = ["gemini"]限制）

- **FR-002**: 系统MUST支持通过配置定义任意provider，配置项包括：provider名称、llm CLI基础命令、模型名称、超时时间、环境变量要求、额外CLI参数

- **FR-003**: 系统MUST提供DeepSeek的默认配置作为新的primary provider，使用标准llm CLI接口（模型名：deepseek-coder或deepseek-chat），完全替代当前的Gemini默认配置

- **FR-004**: 系统MUST验证用户提供的provider配置的完整性，包括：必需环境变量是否存在、CLI命令是否可执行、参数格式是否正确

#### CLI命令拼装

- **FR-005**: 系统MUST能够根据provider配置（cli_command、model_name、additional_args等）拼装出完整的llm CLI命令行

- **FR-006**: 系统MUST支持dry-run模式，输出将要执行的完整命令但不实际执行（用于调试和验证）

- **FR-007**: 系统MUST确保拼装的CLI命令符合llm CLI的标准接口规范（格式：`llm -m <model_name> "<prompt>"`，支持额外参数如--temperature），无需provider特定定制化

#### 环境与验证

- **FR-008**: 系统MUST在执行LLM调用前验证provider所需的环境变量（如DEEPSEEK_API_KEY）是否已设置

- **FR-009**: 系统MUST在validate_prerequisites方法中检查llm CLI是否已安装且可执行（通过执行`llm --version`验证）

- **FR-010**: 系统MUST在环境验证失败时，提供清晰的错误信息，包括：缺失的环境变量名称、llm CLI安装状态、建议的修复步骤

#### 代码清理与迁移

- **FR-011**: 系统MUST在llm-deepseek分支完全移除Gemini专用代码，包括：硬编码的provider验证、Gemini特定的CLI命令拼装逻辑、Gemini相关的测试用例和文档引用

- **FR-012**: 系统MUST将所有LLM调用统一到llm CLI标准接口，后续模型切换（如从deepseek-coder切换到其他模型）通过llm CLI的模型管理机制实现，不在应用层维护provider特定逻辑

#### 错误处理与可观测性

- **FR-013**: 系统MUST在llm CLI执行失败时，立即失败并返回错误，遵循fail-fast原则，错误分类包括：认证失败、超时、无效参数、provider服务不可用，不实现自动重试或降级机制

- **FR-014**: 系统MUST在执行LLM调用前验证prompt长度是否超过provider的context window上限，若超出则直接报错并提示具体限制（如"Prompt长度X tokens超过上限Y tokens"），拒绝执行

- **FR-015**: 系统MUST保留现有的进度指示器功能，在长时间LLM调用时向用户展示进度

- **FR-016**: 系统MUST记录实际执行的llm CLI命令（隐藏敏感信息如API密钥）到日志中，便于问题排查

### Key Entities *(include if feature involves data)*

- **ProviderConfig**: 表示单个LLM provider的完整配置
  - 属性：provider名称、llm CLI命令、模型标识、超时设置、环境变量映射、额外参数
  - 关系：一个系统可以配置多个ProviderConfig，但每次调用只使用一个

- **CLICommand**: 表示拼装后的完整llm CLI命令
  - 属性：基础命令、模型参数、额外标志、prompt输入
  - 关系：由ProviderConfig生成，传递给CLI执行器

- **EnvironmentValidator**: 验证provider所需环境的实体
  - 属性：必需环境变量列表、CLI可用性状态、验证结果
  - 关系：使用ProviderConfig的环境变量定义进行验证

---

## Review & Acceptance Checklist

### Content Quality
- [x] No implementation details (languages, frameworks, APIs) - 专注于provider配置抽象，未涉及具体代码结构
- [x] Focused on user value and business needs - 明确了支持多provider的业务价值（成本、性能、灵活性）
- [x] Written for non-technical stakeholders - 使用场景描述而非技术术语
- [x] All mandatory sections completed - User Scenarios和Requirements已完成

### Requirement Completeness
- [x] No [NEEDS CLARIFICATION] markers remain - **PASS**: 所有澄清问题已通过2025-10-17 clarification session解决
- [x] Requirements are testable and unambiguous - 所有16个FR均可通过单元测试或集成测试验证
- [x] Success criteria are measurable - 可以通过"能否成功调用DeepSeek生成报告"等明确标准衡量
- [x] Scope is clearly bounded - 限定在llm-deepseek分支，专注于provider抽象，批量场景明确排除
- [x] Dependencies and assumptions identified - 依赖llm CLI标准接口，DeepSeek通过`llm -m deepseek-coder/deepseek-chat`调用

---

## Execution Status

- [x] User description parsed - Linear issue COD-12内容已解析
- [x] Key concepts extracted - provider抽象、CLI统一、DeepSeek集成
- [x] Ambiguities marked - 已标记4个关键决策点
- [x] Ambiguities resolved - 通过2025-10-17 clarification session完成5个问题澄清
- [x] User scenarios defined - 5个acceptance场景 + 4个edge case（已明确处理策略）
- [x] Requirements generated - 16个FR，覆盖配置、验证、代码清理、错误处理
- [x] Entities identified - 3个key entity
- [x] Review checklist passed - **PASS**: 所有关键不确定性已解决，规格完整可测试

---

## Specification Summary

**Clarification Status**: ✅ Complete - All critical ambiguities resolved via clarification session 2025-10-17

**Key Decisions**:
- DeepSeek通过标准llm CLI接口调用（`llm -m deepseek-coder/deepseek-chat`）
- 完全移除Gemini专用代码，llm CLI统一管理模型切换
- 采用fail-fast错误处理策略（无自动重试/降级）
- 超长prompt直接报错（无自动截断）
- MVP不包含批量生成场景（单线程执行）

**Ready for**: `/plan` - 规格已完整且可测试，可进入实现计划阶段
