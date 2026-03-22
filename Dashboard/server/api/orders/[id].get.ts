import { orders } from '~/data/orderData';

export default cachedEventHandler((event) => {
  const id = getRouterParam(event, 'id');
  const order = orders.find(o => o.id === Number(id));
  
  if (!order) {
    throw createError({
      statusCode: 404,
      statusMessage: 'Order not found'
    });
  }

  // Enhance order with additional details for the detail page
  return {
    ...order,
    orderVia: 'Inventar',
    shippingAddress: {
      street: '2118 Thornridge Cir',
      city: 'Syracuse',
      state: 'Connecticut',
      zipCode: '35624'
    },
    products: [
      {
        id: 1,
        name: 'Earnies Chair - Black Leather',
        quantity: 1,
        price: 250.00,
        image: '/logo.png'
      }
    ],
    subtotal: 250.00,
    shipping: 6.00,
    tax: 6.00
  };
});
