
#### **1. Theming and Design System**

Nuxt UI v3 has been rebuilt with a new theming system based on Tailwind CSS v4 and Tailwind Variants.

* **Tailwind CSS v4 Integration**: Configuration is now CSS-first, using the `@theme` directive in your main CSS file to define custom design tokens like fonts, colors, and breakpoints.
* **Color System**: The library uses a design system with 7 primary color aliases: `primary`, `secondary`, `success`, `info`, `warning`, `error`, and `neutral`. The default `gray` color from v2 has been renamed to `neutral`.
    * You can configure these color aliases in your `app.config.ts` (for Nuxt) or `vite.config.ts` (for Vue).
    * **Example `app.config.ts`:**
        ```ts [app.config.ts]
        export default defineAppConfig({
          ui: {
            colors: {
              primary: 'green',
              neutral: 'slate'
            }
          }
        })
        ```
* **Design Tokens (CSS Variables)**: Nuxt UI provides a robust system of CSS variables for consistent styling.
    * **Background Colors**: Use classes like `bg-default`, `bg-muted`, `bg-elevated`, and `bg-accented`.
    * **Text Colors**: Use classes like `text-default`, `text-dimmed`, `text-muted`, `text-toned`, and `text-highlighted`.
    * **Example Usage**:
        ```vue
        <template>
          <div class="bg-muted text-default">
            <p class="text-highlighted">Highlighted Text</p>
            <p class="text-muted">Muted Text</p>
          </div>
        </template>
        ```

#### **2. Component Customization**

* **Tailwind Variants**: Component styling is now managed via the Tailwind Variants API.
* **`ui` prop**: To override specific component slots, use the `ui` prop. This is the primary way to customize component parts.
    * **Example**:
        ```vue
        <template>
          <UButton :ui="{ base: 'font-bold' }" />
        </template>
        ```
* **`class` prop**: To add classes to the root element of a component, use the standard `class` prop.
* **Global Overrides (`app.config.ts`)**: You can override component themes globally in your `app.config.ts` file.
    * **Example `app.config.ts` for Button**:
        ```ts [app.config.ts]
        export default defineAppConfig({
            ui: {
              button: {
                slots: {
                  base: 'font-medium'
                },
                defaultVariants: {
                  size: 'md',
                  color: 'primary'
                }
              }
            }
        })
        ```

### Component Examples

#### **UBadge**

A component to display a badge.

* **Basic Usage**:
    ```vue
    <template>
      <UBadge label="Badge" />
    </template>
    ```
* **Variants**:
    ```vue
    <template>
      <div class="flex gap-4">
        <UBadge label="Solid" variant="solid" />
        <UBadge label="Outline" variant="outline" />
        <UBadge label="Soft" variant="soft" />
        <UBadge label="Subtle" variant="subtle" />
      </div>
    </template>
    ```
* **Colors & Sizes**:
    ```vue
    <template>
      <div class="flex items-center gap-4">
        <UBadge label="Error" color="error" size="lg" />
        <UBadge label="Success" color="success" size="md" />
        <UBadge label="Neutral" color="neutral" size="sm" />
      </div>
    </template>
    ```
* **With Icon and Avatar**:
    ```vue
    <template>
      <div class="flex items-center gap-4">
        <UBadge icon="i-lucide-rocket" label="Rocket" />
        <UBadge :avatar="{ src: 'https://github.com/nuxt.png' }" label="Nuxt" />
      </div>
    </template>
    ```
    

#### **UButton**

A versatile button component.

* **Basic Usage**:
    ```vue
    <template>
      <UButton label="Click Me" />
    </template>
    ```
* **Variants & Colors**:
    ```vue
    <template>
      <div class="flex gap-4">
        <UButton label="Primary" />
        <UButton label="Neutral Outline" color="neutral" variant="outline" />
        <UButton label="Success Ghost" color="success" variant="ghost" />
        <UButton label="Error Link" color="error" variant="link" />
      </div>
    </template>
    ```
    
* **Sizes**:
    ```vue
    <template>
      <div class="flex items-center gap-4">
        <UButton label="Large" size="lg" />
        <UButton label="Medium" size="md" />
        <UButton label="Small" size="sm" />
      </div>
    </template>
    ```
    
* **With Icons & Loading State**:
    ```vue
    <template>
      <div class="flex items-center gap-4">
        <UButton icon="i-lucide-rocket" label="Launch" />
        <UButton trailing-icon="i-lucide-arrow-right" label="Next" />
        <UButton loading label="Loading..." />
        <UButton loading-auto :trailing="false" @click="() => new Promise(r => setTimeout(r, 1000))">
          Click to Load
        </UButton>
      </div>
    </template>
    ```
    
* **As a Link**:
    ```vue
    <template>
      <UButton label="Go to GitHub" to="https://github.com/nuxt/ui" target="_blank" />
    </template>
    ```
    

#### **UInput**

A form input element.

* **Basic Usage**:
    ```vue
    <script setup>
      const value = ref('');
    </script>
    <template>
      <UInput v-model="value" placeholder="Enter your email..." />
    </template>
    ```
* **Variants & Colors**:
    ```vue
    <template>
      <div class="flex flex-col gap-4">
        <UInput placeholder="Outline (Default)" variant="outline" />
        <UInput placeholder="Subtle" variant="subtle" color="neutral" />
      </div>
    </template>
    ```
    
* **Sizes**:
    ```vue
    <template>
      <div class="flex items-center gap-4">
        <UInput placeholder="Large" size="lg" />
        <UInput placeholder="Medium" size="md" />
        <UInput placeholder="Small" size="sm" />
      </div>
    </template>
    ```
    
* **With Icons**:
    ```vue
    <template>
      <div class="flex flex-col gap-4">
        <UInput icon="i-lucide-search" placeholder="Search..." />
        <UInput trailing-icon="i-lucide-at-sign" placeholder="Enter your email" />
      </div>
    </template>
    ```
    
* **With Clear Button**:
    ```vue
    <script setup>
      const value = ref('Click to clear');
    </script>
    <template>
      <UInput v-model="value" :ui="{ trailing: 'pe-1' }">
        <template v-if="value?.length" #trailing>
          <UButton
           color="neutral"
           variant="link"
           size="sm"
           icon="i-lucide-circle-x"
           aria-label="Clear input"
           @click="value = ''"
          />
        </template>
      </UInput>
    </template>
    ```
    

#### **USelect**

A native select component. For a more advanced version with search and custom templates, see `USelectMenu`.

* **Basic Usage with Array of Strings**:
    ```vue
    <script setup>
      const items = ['Backlog', 'Todo', 'In Progress', 'Done'];
      const selected = ref(items[0]);
    </script>
    <template>
      <USelect v-model="selected" :items="items" class="w-48" />
    </template>
    ```
    
* **Usage with Array of Objects**:
    ```vue
    <script setup>
      const items = [
        { label: 'Backlog', id: 'backlog' },
        { label: 'Todo', id: 'todo' },
        { label: 'In Progress', id: 'in_progress' },
        { label: 'Done', id: 'done' },
      ];
      const selected = ref('todo');
    </script>
    <template>
      <USelect v-model="selected" :items="items" value-key="id" label-key="label" class="w-48" />
    </template>
    ```
    
* **With Icon**:
    ```vue
    <template>
      <USelect :items="['Option 1', 'Option 2']" icon="i-lucide-list-filter" class="w-48" />
    </template>
    ```
    

#### **UForm & UFormField**

A set of components to handle form validation and display.

* **Functionality**:
    * `UForm` handles form state and validation using a schema (Zod, Valibot, Yup, etc.) or a custom validation function.
    * `UFormField` wraps a form input, displaying labels, hints, and error messages.
    * The `name` prop of `UFormField` links it to the validation rules in the form's schema.
* **Complete Example with Zod**:
    ```vue
    <script setup lang="ts">
    import { z } from 'zod';
    import type { FormSubmitEvent } from '@nuxt/ui';

    // 1. Define the validation schema
    const schema = z.object({
      email: z.string().email('Invalid email address'),
      password: z.string().min(8, 'Password must be at least 8 characters')
    });

    type Schema = z.output<typeof schema>;

    // 2. Define the reactive state
    const state = reactive({
      email: '',
      password: ''
    });

    // 3. Handle the submit event
    const toast = useToast();
    async function onSubmit(event: FormSubmitEvent<Schema>) {
      toast.add({ title: 'Success!', description: 'The form was submitted.' });
      console.log(event.data);
    }
    </script>

    <template>
      <UForm :schema="schema" :state="state" class="space-y-4" @submit="onSubmit">
        <UFormField label="Email" name="email">
          <UInput v-model="state.email" />
        </UFormField>

        <UFormField label="Password" name="password">
          <UInput v-model="state.password" type="password" />
        </UFormField>

        <UButton type="submit">
          Submit
        </UButton>
      </UForm>
    </template>
    ```
    

#### **UTable**

A powerful and customizable table component for displaying data.

* **Core Concepts**:
    * **`:data`**: Takes an array of objects, where each object represents a row.
    * **`:columns`**: An array that defines the table's columns. Each column object uses an `accessorKey` to link to a property in the data objects.
    * **Custom Rendering**: The `header` and `cell` properties within a column definition can use Vue's `h` render function to display custom components (like `UBadge` and `UButton`), apply complex formatting, or create interactive elements.
    * **Sorting**: Sorting can be enabled and controlled by binding a state variable to the `v-model:sorting` prop.
* **Advanced Example with Custom Rendering and Sorting**:

    This example showcases a table with formatted dates, custom badges for status, a sortable email header, and right-aligned, currency-formatted amounts.
    ```vue
    <script setup lang="ts">
    import { h, resolveComponent } from 'vue'
    import type { TableColumn } from '@nuxt/ui'

    const UBadge = resolveComponent('UBadge')
    const UButton = resolveComponent('UButton')

    type Payment = {
      id: string
      date: string
      status: 'paid' | 'failed' | 'refunded'
      email: string
      amount: number
    }

    const data = ref<Payment[]>([
      {
        id: '4600',
        date: '2024-03-11T15:30:00',
        status: 'paid',
        email: 'james.anderson@example.com',
        amount: 594
      },
      {
        id: '4599',
        date: '2024-03-11T10:10:00',
        status: 'failed',
        email: 'mia.white@example.com',
        amount: 276
      },
      {
        id: '4598',
        date: '2024-03-11T08:50:00',
        status: 'refunded',
        email: 'william.brown@example.com',
        amount: 315
      },
      // ... more data
    ])

    const columns: TableColumn<Payment>[] = [
      {
        accessorKey: 'id',
        header: '#',
        cell: ({ row }) => `#${row.getValue('id')}`
      },
      {
        accessorKey: 'date',
        header: 'Date',
        cell: ({ row }) => {
          return new Date(row.getValue('date')).toLocaleString('en-US', {
            day: 'numeric',
            month: 'short',
            hour: '2-digit',
            minute: '2-digit',
            hour12: false
          })
        }
      },
      {
        accessorKey: 'status',
        header: 'Status',
        cell: ({ row }) => {
          const color = {
            paid: 'success' as const,
            failed: 'error' as const,
            refunded: 'neutral' as const
          }[row.getValue('status') as string]

          return h(UBadge, { class: 'capitalize', variant: 'subtle', color }, () =>
            row.getValue('status')
          )
        }
      },
      {
        accessorKey: 'email',
        header: ({ column }) => {
          const isSorted = column.getIsSorted()

          return h(UButton, {
            color: 'neutral',
            variant: 'ghost',
            label: 'Email',
            icon: isSorted
              ? isSorted === 'asc'
                ? 'i-lucide-arrow-up-narrow-wide'
                : 'i-lucide-arrow-down-wide-narrow'
              : 'i-lucide-arrow-up-down',
            class: '-mx-2.5',
            onClick: () => column.toggleSorting(column.getIsSorted() === 'asc')
          })
        }
      },
      {
        accessorKey: 'amount',
        header: () => h('div', { class: 'text-right' }, 'Amount'),
        cell: ({ row }) => {
          const amount = Number.parseFloat(row.getValue('amount'))
          const formatted = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'EUR'
          }).format(amount)
          return h('div', { class: 'text-right font-medium' }, formatted)
        }
      }
    ]

    const sorting = ref([
      {
        id: 'email',
        desc: false
      }
    ])
    </script>

    <template>
      <UTable v-model:sorting="sorting" :data="data" :columns="columns" class="flex-1" />
    </template>
    ```

