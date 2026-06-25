app_name = "vortexus_ecommerce_integration"
app_title = "Vortexus Ecommerce Integration"
app_publisher = "ambundo-ronald"
app_description = "ERPNext ecommerce bridge for the Vortexus storefront"
app_email = "support@vortexusindustrial.com"
app_license = "MIT"

after_install = "vortexus_ecommerce_integration.install.after_install"

doc_events = {
    "Sales Order": {
        "on_submit": "vortexus_ecommerce_integration.events.sales_order.on_submit",
    },
}
